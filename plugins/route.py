import asyncio
import html
import secrets
import socket
import time
from aiohttp import web
from config import ANTI_BYPASS_BLOCK_SCORE, ANTI_BYPASS_MIN_WAIT
from database.database import db

routes = web.RouteTableDef()

# ── In-memory stores ───────────────────────────────────────────────────────────
# nonce store: (user_id, token) → (nonce, challenge, created_at)
_nonces: dict = {}
# per-user fail counter: user_id → (count, first_fail_ts)
_fail_counter: dict = {}

FAIL_LIMIT   = 5    # max failed /go attempts per user
FAIL_WINDOW  = 300  # seconds (5 min)
NONCE_TTL    = 600  # seconds (10 min)

def _clean_stores():
    now = time.time()
    for k in list(_nonces):
        if now - _nonces[k][2] > NONCE_TTL:
            _nonces.pop(k, None)
    for uid in list(_fail_counter):
        count, ts = _fail_counter[uid]
        if now - ts > FAIL_WINDOW:
            _fail_counter.pop(uid, None)

def _record_fail(user_id: int) -> bool:
    """Return True if user should be rate-limited."""
    now = time.time()
    count, ts = _fail_counter.get(user_id, (0, now))
    if now - ts > FAIL_WINDOW:
        count, ts = 0, now
    count += 1
    _fail_counter[user_id] = (count, ts)
    return count > FAIL_LIMIT

# ── Suspicious signals ─────────────────────────────────────────────────────────
SUSPICIOUS_USER_AGENTS = (
    "python", "requests", "curl", "wget", "axios", "node-fetch", "go-http-client",
    "headless", "selenium", "playwright", "phantomjs", "scrapy", "spider", "crawler",
    "bot", "httpclient", "java/",
)
DATACENTER_KEYWORDS = (
    "amazon", "aws", "google", "cloud", "azure", "microsoft", "digitalocean",
    "hetzner", "ovh", "linode", "vultr", "contabo", "oracle", "alibaba",
    "tencent", "leaseweb", "host", "server", "colo", "datacenter", "replit",
    "railway", "render", "koyeb",
)

# ── Helpers ────────────────────────────────────────────────────────────────────
def get_ip(request):
    for header in ("X-Forwarded-For", "X-Real-IP"):
        val = request.headers.get(header, "")
        if val:
            return val.split(",")[0].strip()
    peer = request.transport.get_extra_info("peername")
    return peer[0] if peer else ""

async def get_rdns(ip):
    if not ip:
        return ""
    try:
        return await asyncio.wait_for(asyncio.to_thread(socket.gethostbyaddr, ip), timeout=1.5)
    except Exception:
        return ""

async def get_risk(request, created_at, post_data: dict):
    ip          = get_ip(request)
    user_agent  = request.headers.get("User-Agent", "")
    ua_lower    = user_agent.lower()
    score       = 0
    reasons     = []

    # ── User-agent check ───────────────────────────────────────────────────────
    if not user_agent:
        score += 30; reasons.append("missing_ua")
    elif any(w in ua_lower for w in SUSPICIOUS_USER_AGENTS):
        score += 35; reasons.append("suspicious_ua")

    # ── Timing check ──────────────────────────────────────────────────────────
    elapsed = time.time() - float(created_at or time.time())
    if elapsed < ANTI_BYPASS_MIN_WAIT:
        score += 40; reasons.append("too_fast")

    # ── JS fingerprint (sent by the page) ─────────────────────────────────────
    webdriver  = post_data.get("_wd", "1")   # "1" = bot, "0" = real
    languages  = post_data.get("_la", "0")   # language count
    sw         = post_data.get("_sw", "0")   # screen width
    challenge_answer = post_data.get("_ca", "")
    honeypot   = post_data.get("_hp", "MISSING")

    if honeypot != "":                        # bots fill hidden fields
        score += 60; reasons.append("honeypot_filled")
    if webdriver == "1":
        score += 50; reasons.append("webdriver_detected")
    try:
        if int(languages) == 0:
            score += 25; reasons.append("no_browser_languages")
        if int(sw) < 100:
            score += 20; reasons.append("suspicious_screen_width")
    except Exception:
        score += 20; reasons.append("missing_fp")

    # ── IP reuse check ────────────────────────────────────────────────────────
    ip_count, ua_count = await db.count_recent_verify_attempts(ip=ip, user_agent=user_agent)
    if ip_count >= 30:
        score += 50; reasons.append("high_ip_reuse")
    elif ip_count >= 10:
        score += 25; reasons.append("ip_reuse")
    if ua_count >= 50:
        score += 25; reasons.append("high_ua_reuse")

    # ── Datacenter RDNS ───────────────────────────────────────────────────────
    rdns = await get_rdns(ip)
    rdns_text = " ".join([rdns[0], *rdns[1]]) if isinstance(rdns, tuple) else str(rdns)
    if rdns_text and any(w in rdns_text.lower() for w in DATACENTER_KEYWORDS):
        score += 35; reasons.append("datacenter_ip")

    return score, reasons, ip, user_agent, elapsed

# ── Error HTML helpers ─────────────────────────────────────────────────────────
def _err_page(title: str, msg: str, status: int):
    body = f"""<!doctype html><html><head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>
body{{font-family:Arial,sans-serif;background:#0f172a;color:#e5e7eb;
     display:flex;min-height:100vh;align-items:center;justify-content:center;margin:0}}
.card{{max-width:400px;background:#111827;border:1px solid #334155;border-radius:18px;
       padding:30px;text-align:center;box-shadow:0 20px 60px #0008}}
.icon{{font-size:3rem;margin-bottom:12px}}
h2{{margin:0 0 10px;color:#f87171}}
p{{color:#94a3b8;font-size:14px;line-height:1.6}}
</style></head><body>
<div class="card">
  <div class="icon">{'🚫' if status == 403 else '⏳' if status == 429 else '⚠️'}</div>
  <h2>{title}</h2>
  <p>{msg}</p>
</div></body></html>"""
    return web.Response(text=body, content_type="text/html", status=status)

# ── Verify page ────────────────────────────────────────────────────────────────
def verify_page(user_id, token, bot_username, wait_seconds, nonce, challenge):
    safe_bot   = html.escape(bot_username)
    go_url     = f"/verify/{int(user_id)}/{html.escape(token)}/{safe_bot}/go"
    safe_nonce = html.escape(nonce)
    # challenge answer = (challenge * 7 + 13) computed in JS, verified server-side
    return web.Response(content_type="text/html", text=f"""<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Human Verification</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Segoe UI',Arial,sans-serif;background:linear-gradient(135deg,#0f172a 0%,#1e293b 100%);
     color:#e5e7eb;display:flex;min-height:100vh;align-items:center;justify-content:center}}
.card{{width:92%;max-width:400px;background:#111827;border:1px solid #1e3a5f;
       border-radius:20px;padding:32px 24px;text-align:center;
       box-shadow:0 25px 70px rgba(0,0,0,.6)}}
.shield{{font-size:3rem;margin-bottom:8px;animation:pulse 2s infinite}}
@keyframes pulse{{0%,100%{{transform:scale(1)}}50%{{transform:scale(1.08)}}}}
h2{{font-size:1.3rem;margin-bottom:6px;color:#60a5fa}}
.sub{{color:#64748b;font-size:13px;margin-bottom:24px}}
.prog-wrap{{background:#1e293b;border-radius:99px;height:8px;overflow:hidden;margin-bottom:10px}}
.prog-bar{{height:100%;border-radius:99px;
           background:linear-gradient(90deg,#3b82f6,#22c55e);
           transition:width .9s linear;width:0%}}
.num{{font-size:2rem;font-weight:700;color:#22c55e;margin:8px 0}}
.hint{{color:#475569;font-size:12px;margin-top:4px}}
.msg{{color:#22c55e;font-size:15px;font-weight:600;margin-top:16px;display:none}}
</style>
</head>
<body>
<div class="card">
  <div class="shield">🛡️</div>
  <h2>Human Verification</h2>
  <p class="sub">Verifying your session&hellip;</p>
  <div class="prog-wrap"><div class="prog-bar" id="bar"></div></div>
  <div class="num" id="left">{int(wait_seconds)}</div>
  <div class="hint">Please wait while we confirm you are human</div>
  <p class="msg" id="msg">✅ Redirecting&hellip;</p>
  <form id="gf" action="{go_url}" method="POST" style="display:none">
    <input type="hidden" name="n"   value="{safe_nonce}">
    <input type="hidden" name="_wd" id="_wd" value="1">
    <input type="hidden" name="_la" id="_la" value="0">
    <input type="hidden" name="_sw" id="_sw" value="0">
    <input type="hidden" name="_ca" id="_ca" value="">
    <input type="hidden" name="_hp" id="_hp" value="">
  </form>
</div>
<script>
(function(){{
  var total = {int(wait_seconds)} || 1;
  var left  = total;
  var bar   = document.getElementById("bar");
  var label = document.getElementById("left");
  var msg   = document.getElementById("msg");
  var ch    = {challenge};

  // Fill fingerprint fields immediately
  document.getElementById("_wd").value = (navigator.webdriver) ? "1" : "0";
  document.getElementById("_la").value = (navigator.languages || []).length;
  document.getElementById("_sw").value = screen.width || 0;
  document.getElementById("_ca").value = Math.floor(ch * 7 + 13);
  // honeypot must stay empty — bots fill it automatically

  bar.style.width = "0%";

  var timer = setInterval(function(){{
    left -= 1;
    var pct = ((total - left) / total * 100).toFixed(1);
    bar.style.width = pct + "%";
    if (left <= 0) {{
      clearInterval(timer);
      bar.style.width = "100%";
      label.style.display = "none";
      msg.style.display = "block";
      document.getElementById("gf").submit();
    }} else {{
      label.textContent = left;
    }}
  }}, 1000);
}})();
</script>
</body>
</html>""")

# ── Routes ─────────────────────────────────────────────────────────────────────
@routes.get("/", allow_head=True)
async def root_route_handler(request):
    return web.json_response("Yae Miko")

@routes.get("/verify/{user_id}/{token}/{bot_username}", allow_head=True)
async def verify_route_handler(request):
    try:
        user_id      = int(request.match_info["user_id"])
        token        = request.match_info["token"]
        bot_username = request.match_info["bot_username"]

        status = await db.get_verify_status(user_id)
        if status.get("verify_token") != token:
            return _err_page("Invalid Token",
                "This verification link is invalid or has already expired.<br>Please request a new link from the bot.",
                403)

        created_at   = status.get("created_at") or time.time()
        elapsed      = time.time() - float(created_at)
        wait_seconds = max(ANTI_BYPASS_MIN_WAIT - int(elapsed), 0)

        _clean_stores()

        # Rate-limit: too many fails from this user?
        count, ts = _fail_counter.get(user_id, (0, time.time()))
        if count > FAIL_LIMIT and time.time() - ts < FAIL_WINDOW:
            return _err_page("Too Many Attempts",
                "You have too many failed verification attempts.<br>Please wait 5 minutes and try again.",
                429)

        nonce     = secrets.token_urlsafe(24)
        challenge = secrets.randbelow(90000) + 10000   # 5-digit random int
        _nonces[(user_id, token)] = (nonce, challenge, time.time())

        return verify_page(user_id, token, bot_username, wait_seconds, nonce, challenge)
    except web.HTTPException:
        raise
    except Exception:
        return _err_page("Error", "An unexpected error occurred. Please try again.", 500)

@routes.post("/verify/{user_id}/{token}/{bot_username}/go")
async def verify_go_route_handler(request):
    try:
        user_id      = int(request.match_info["user_id"])
        token        = request.match_info["token"]
        bot_username = request.match_info["bot_username"]

        # ── Nonce validation ───────────────────────────────────────────────────
        try:
            post_data = dict(await request.post())
        except Exception:
            post_data = {}

        submitted_nonce = post_data.get("n", "")
        stored = _nonces.pop((user_id, token), None)

        if not stored or stored[0] != submitted_nonce:
            if _record_fail(user_id):
                return _err_page("Too Many Attempts",
                    "Too many failed attempts. Please wait 5 minutes.", 429)
            return _err_page("Session Invalid",
                "Your session is invalid. Please open the verification link again in your browser.",
                403)

        nonce, challenge, nonce_ts = stored

        # ── Challenge verification ─────────────────────────────────────────────
        try:
            expected_ca = str(int(challenge * 7 + 13))
        except Exception:
            expected_ca = ""
        if post_data.get("_ca", "") != expected_ca:
            _record_fail(user_id)
            return _err_page("Bot Detected",
                "JavaScript challenge failed. Please open the link in a real browser.",
                403)

        # ── Token check ────────────────────────────────────────────────────────
        status = await db.get_verify_status(user_id)
        if status.get("verify_token") != token:
            return _err_page("Invalid Token",
                "This token is invalid or has already been used.", 403)

        # ── Risk scoring ───────────────────────────────────────────────────────
        score, reasons, ip, user_agent, elapsed = await get_risk(
            request, status.get("created_at"), post_data
        )
        passed = score < ANTI_BYPASS_BLOCK_SCORE and elapsed >= ANTI_BYPASS_MIN_WAIT
        await db.log_verify_attempt(user_id, token, ip, user_agent, passed, score, reasons)

        if not passed:
            _record_fail(user_id)
            return _err_page("Suspicious Activity Detected",
                f"Automated or suspicious behavior was detected (score: {score}).<br>"
                "Please open the link normally in a real browser.",
                429)

        # ── Human check passed: save flag but do NOT set is_verified yet ─────────
        # is_verified only becomes True after user completes shortener + sends verify_ token to bot
        marked = await db.mark_web_verified(user_id, token, ip, user_agent, score, reasons)
        if not marked:
            return _err_page("Token Expired",
                "This token has already been used or expired. Please request a new one from the bot.",
                403)

        shortlink = status.get("link") or ""
        if not shortlink:
            return _err_page("Configuration Error",
                "Shortener is not configured. Please contact the bot owner.", 500)
        raise web.HTTPFound(shortlink)

    except web.HTTPException:
        raise
    except Exception:
        return _err_page("Error", "An unexpected error occurred. Please try again.", 500)
