import asyncio
import html
import secrets
import socket
import time
from aiohttp import web
from config import ANTI_BYPASS_BLOCK_SCORE, ANTI_BYPASS_MIN_WAIT
from database.database import db

routes = web.RouteTableDef()

# In-memory nonce store: (user_id, token) -> (nonce, created_at)
# Nonces expire after 10 minutes and are one-time use
_nonces: dict = {}

def _clean_nonces():
    now = time.time()
    expired = [k for k, v in _nonces.items() if now - v[1] > 600]
    for k in expired:
        _nonces.pop(k, None)

@routes.get("/", allow_head=True)
async def root_route_handler(request):
    return web.json_response("Yae Miko")

SUSPICIOUS_USER_AGENTS = (
    "python", "requests", "curl", "wget", "axios", "node-fetch", "go-http-client",
    "headless", "selenium", "playwright", "phantomjs", "scrapy", "spider", "crawler",
    "bot", "httpclient", "java/"
)

DATACENTER_KEYWORDS = (
    "amazon", "aws", "google", "cloud", "azure", "microsoft", "digitalocean",
    "hetzner", "ovh", "linode", "vultr", "contabo", "oracle", "alibaba",
    "tencent", "leaseweb", "host", "server", "colo", "datacenter", "replit",
    "railway", "render", "koyeb"
)

def get_ip(request):
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    peer = request.transport.get_extra_info("peername")
    return peer[0] if peer else ""

async def get_rdns(ip):
    if not ip:
        return ""
    try:
        return await asyncio.wait_for(asyncio.to_thread(socket.gethostbyaddr, ip), timeout=1.5)
    except Exception:
        return ""

async def get_risk(request, created_at):
    ip = get_ip(request)
    user_agent = request.headers.get("User-Agent", "")
    ua_lower = user_agent.lower()
    score = 0
    reasons = []

    if not user_agent:
        score += 25
        reasons.append("missing_user_agent")
    elif any(word in ua_lower for word in SUSPICIOUS_USER_AGENTS):
        score += 35
        reasons.append("suspicious_user_agent")

    elapsed = time.time() - float(created_at or time.time())
    if elapsed < ANTI_BYPASS_MIN_WAIT:
        score += 40
        reasons.append("too_fast")

    ip_count, ua_count = await db.count_recent_verify_attempts(ip=ip, user_agent=user_agent)
    if ip_count >= 30:
        score += 50
        reasons.append("high_ip_reuse")
    elif ip_count >= 10:
        score += 25
        reasons.append("ip_reuse")

    if ua_count >= 50:
        score += 25
        reasons.append("high_user_agent_reuse")

    rdns = await get_rdns(ip)
    rdns_text = " ".join([rdns[0], *rdns[1]]) if isinstance(rdns, tuple) else str(rdns)
    if rdns_text and any(word in rdns_text.lower() for word in DATACENTER_KEYWORDS):
        score += 35
        reasons.append("datacenter_ip")

    return score, reasons, ip, user_agent, elapsed

def verify_page(user_id, token, bot_username, wait_seconds, nonce):
    safe_bot = html.escape(bot_username)
    go_url = f"/verify/{int(user_id)}/{html.escape(token)}/{safe_bot}/go"
    safe_nonce = html.escape(nonce)
    return web.Response(
        text=f"""
<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Verify Token</title>
<style>
body{{font-family:Arial,sans-serif;background:#0f172a;color:#e5e7eb;display:flex;min-height:100vh;align-items:center;justify-content:center;margin:0}}
.card{{max-width:420px;background:#111827;border:1px solid #334155;border-radius:18px;padding:26px;text-align:center;box-shadow:0 20px 60px #0008}}
.ring{{width:80px;height:80px;margin:0 auto 18px;border-radius:50%;border:6px solid #334155;border-top-color:#22c55e;animation:spin 1s linear infinite}}
@keyframes spin{{to{{transform:rotate(360deg)}}}}
.num{{font-size:2.2rem;font-weight:700;color:#22c55e;margin:8px 0}}
.small{{color:#94a3b8;font-size:14px;line-height:1.5}}
.msg{{color:#22c55e;font-size:15px;font-weight:600;display:none}}
</style>
</head>
<body>
<div class="card">
<div class="ring"></div>
<div class="num" id="left">{int(wait_seconds)}</div>
<p class="small">Please wait while we verify your session&hellip;</p>
<p class="msg" id="msg">Redirecting to Telegram&hellip;</p>
<form id="gf" action="{go_url}" method="POST" style="display:none">
<input type="hidden" name="n" value="{safe_nonce}">
</form>
</div>
<script>
let left = {int(wait_seconds)};
const label = document.getElementById("left");
const msg = document.getElementById("msg");
const timer = setInterval(() => {{
  left -= 1;
  if (left <= 0) {{
    clearInterval(timer);
    label.style.display = "none";
    msg.style.display = "block";
    document.getElementById("gf").submit();
  }} else {{
    label.textContent = left;
  }}
}}, 1000);
</script>
</body>
</html>
""",
        content_type="text/html"
    )

@routes.get("/verify/{user_id}/{token}/{bot_username}", allow_head=True)
async def verify_route_handler(request):
    try:
        user_id = int(request.match_info["user_id"])
        token = request.match_info["token"]
        bot_username = request.match_info["bot_username"]
        status = await db.get_verify_status(user_id)
        if status.get("verify_token") != token:
            return web.Response(text="Invalid or expired token.", status=403)
        created_at = status.get("created_at") or time.time()
        elapsed = time.time() - float(created_at)
        wait_seconds = max(ANTI_BYPASS_MIN_WAIT - int(elapsed), 0)

        # Generate a one-time nonce for this page load
        _clean_nonces()
        nonce = secrets.token_urlsafe(24)
        _nonces[(user_id, token)] = (nonce, time.time())

        return verify_page(user_id, token, bot_username, wait_seconds, nonce)
    except Exception:
        return web.Response(text="Verification failed.", status=500)

@routes.post("/verify/{user_id}/{token}/{bot_username}/go")
async def verify_go_route_handler(request):
    try:
        user_id = int(request.match_info["user_id"])
        token = request.match_info["token"]
        bot_username = request.match_info["bot_username"]

        # Validate nonce — must come from the actual verify page form
        try:
            post_data = await request.post()
            submitted_nonce = post_data.get("n", "")
        except Exception:
            submitted_nonce = ""

        stored = _nonces.pop((user_id, token), None)
        if not stored or stored[0] != submitted_nonce:
            return web.Response(
                text="Verification failed: invalid session. Please open the link again in your browser.",
                status=403
            )

        status = await db.get_verify_status(user_id)
        if status.get("verify_token") != token:
            return web.Response(text="Invalid or expired token.", status=403)

        score, reasons, ip, user_agent, elapsed = await get_risk(request, status.get("created_at"))
        passed = score < ANTI_BYPASS_BLOCK_SCORE and elapsed >= ANTI_BYPASS_MIN_WAIT
        await db.log_verify_attempt(user_id, token, ip, user_agent, passed, score, reasons)

        if not passed:
            return web.Response(
                text="Suspicious verification blocked. Please open the link normally in your browser and wait before continuing.",
                status=429
            )

        marked = await db.mark_verify_passed(user_id, token, ip, user_agent, score, reasons)
        if not marked:
            return web.Response(text="Invalid or expired token.", status=403)

        shortlink = status.get("link") or ""
        if shortlink:
            raise web.HTTPFound(shortlink)
        raise web.HTTPFound(f"https://telegram.dog/{bot_username}?start=verify_{token}")
    except web.HTTPException:
        raise
    except Exception:
        return web.Response(text="Verification failed.", status=500)
