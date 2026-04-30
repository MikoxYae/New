# ──────────────────────────────────────────────────────────────────────────────
#  Live UPI / Sellgram credentials rotation
#
#  Two owner-only commands:
#
#     /rotate_upi <new_upi> <new_api_key>
#         • Validates inputs (UPI must look like "name@handle", key must be
#           ≥ 16 alphanumeric chars).
#         • Rewrites the constants inside plugins/premium_auto.py and
#           plugins/admin_orders.py using a regex (so changes survive a
#           bot restart).
#         • Monkey-patches the same module attributes IN-MEMORY so the
#           change is live immediately — NO restart required.
#         • Replies with a confirmation showing OLD vs NEW values
#           (API key is masked).
#
#     /show_creds
#         • Shows the currently-active UPI and a masked API key.
#         • Useful right after /rotate_upi to verify the swap landed.
#
#  Both commands are gated on filters.user(OWNER_ID) so even DB-registered
#  admins cannot run them — only the configured OWNER.
# ──────────────────────────────────────────────────────────────────────────────

import os
import re

from pyrogram import Client, filters
from pyrogram.types import Message

from bot import Bot
from config import OWNER_ID

# We import the modules so we can monkey-patch their module-level constants
# at runtime. Because every call site looks up the name fresh on each call
# (not captured into a closure), patching the attribute is enough.
import plugins.premium_auto as _pa
import plugins.admin_orders as _ao


# ═════════════════════════════════════════════════════════════════════════════
#  Helpers
# ═════════════════════════════════════════════════════════════════════════════

# Both source files live next to this file. We resolve once at import time so
# we never accidentally write to the wrong location regardless of CWD.
_PLUGINS_DIR = os.path.dirname(os.path.abspath(__file__))
_PA_PATH = os.path.join(_PLUGINS_DIR, "premium_auto.py")
_AO_PATH = os.path.join(_PLUGINS_DIR, "admin_orders.py")

# Loose VPA validation: <local-part>@<handle>. Local part allows letters,
# digits, dot, dash, underscore. Handle is similar. Telegram users will paste
# real Paytm/PhonePe/GPay VPAs so we keep this permissive.
_UPI_RE = re.compile(r"^[A-Za-z0-9._\-]{2,64}@[A-Za-z0-9._\-]{2,32}$")

# API key sanity check. Sellgram keys are URL-safe alphanumeric strings,
# typically 24 chars. We allow 16-128 to be future-proof.
_KEY_RE = re.compile(r"^[A-Za-z0-9_\-]{16,128}$")


def _mask_key(key: str) -> str:
    """Show only the first 4 + last 4 chars of an API key (for display)."""
    if not key:
        return "<empty>"
    if len(key) <= 8:
        return "*" * len(key)
    return f"{key[:4]}{'*' * (len(key) - 8)}{key[-4:]}"


def _replace_constant(source: str, name: str, new_value: str) -> tuple[str, bool]:
    """
    Replace `NAME = "..."` (any whitespace, any quote style) with
    `NAME = "<new_value>"`. Returns (new_source, replaced_bool).
    """
    # Match assignments of NAME with either single or double quoted string.
    # We only replace the FIRST occurrence to be safe.
    pattern = re.compile(
        rf'^(\s*{re.escape(name)}\s*=\s*)(["\']).*?\2',
        re.MULTILINE,
    )
    found = {"hit": False}

    def _sub(m):
        if found["hit"]:
            return m.group(0)
        found["hit"] = True
        # Preserve the indentation/prefix, swap value, force double quotes.
        return f'{m.group(1)}"{new_value}"'

    new_source = pattern.sub(_sub, source, count=1)
    return new_source, found["hit"]


def _patch_file(path: str, swaps: dict[str, str]) -> dict[str, bool]:
    """
    Apply multiple constant swaps to one file. Returns {name: replaced_bool}.
    Writes the file only if at least one swap took effect.
    """
    with open(path, "r", encoding="utf-8") as f:
        src = f.read()
    results: dict[str, bool] = {}
    new_src = src
    for name, value in swaps.items():
        new_src, hit = _replace_constant(new_src, name, value)
        results[name] = hit
    if any(results.values()) and new_src != src:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_src)
    return results


# ═════════════════════════════════════════════════════════════════════════════
#  /rotate_upi  <new_upi>  <new_api_key>
# ═════════════════════════════════════════════════════════════════════════════
@Bot.on_message(
    filters.command("rotate_upi") & filters.private & filters.user(OWNER_ID)
)
async def rotate_upi_cmd(client: Client, message: Message):
    parts = (message.text or "").split()
    if len(parts) != 3:
        await message.reply_text(
            "<b>ᴜsᴀɢᴇ:</b> <code>/rotate_upi &lt;new_upi&gt; &lt;new_api_key&gt;</code>\n\n"
            "<i>ᴇxᴀᴍᴘʟᴇ:</i>\n"
            "<code>/rotate_upi paytm.s20gmbu@pty 8Mv3zQgQZNVCdU4iBaAFvtu8</code>\n\n"
            "ʙᴏᴛʜ ᴀʀɢᴜᴍᴇɴᴛs ᴀʀᴇ ʀᴇǫᴜɪʀᴇᴅ. ᴜᴘɪ ᴍᴜsᴛ ʟᴏᴏᴋ ʟɪᴋᴇ "
            "<code>name@handle</code> ᴀɴᴅ ᴋᴇʏ ᴍᴜsᴛ ʙᴇ 16-128 ᴀʟᴘʜᴀɴᴜᴍᴇʀɪᴄ.",
            quote=True,
        )
        return

    _, new_upi, new_key = parts

    # ── validation ────────────────────────────────────────────────────────
    if not _UPI_RE.match(new_upi):
        await message.reply_text(
            f"❌ ɪɴᴠᴀʟɪᴅ ᴜᴘɪ: <code>{new_upi}</code>\n"
            f"ᴇxᴘᴇᴄᴛᴇᴅ ғᴏʀᴍᴀᴛ: <code>name@handle</code>",
            quote=True,
        )
        return
    if not _KEY_RE.match(new_key):
        await message.reply_text(
            "❌ ɪɴᴠᴀʟɪᴅ ᴀᴘɪ ᴋᴇʏ. ᴍᴜsᴛ ʙᴇ 16-128 ᴜʀʟ-sᴀғᴇ ᴀʟᴘʜᴀɴᴜᴍᴇʀɪᴄ "
            "ᴄʜᴀʀᴀᴄᴛᴇʀs (ʟᴇᴛᴛᴇʀs, ᴅɪɢɪᴛs, _, -).",
            quote=True,
        )
        return

    # ── snapshot OLD values BEFORE patching ──────────────────────────────
    old_upi = getattr(_pa, "UPI_ID", "?")
    old_key = getattr(_pa, "SELLGRAM_API_KEY", "?")

    if new_upi == old_upi and new_key == old_key:
        await message.reply_text(
            "ℹ️ ᴄʀᴇᴅᴇɴᴛɪᴀʟs ᴀʀᴇ ᴀʟʀᴇᴀᴅʏ sᴇᴛ ᴛᴏ ᴛʜᴇsᴇ ᴠᴀʟᴜᴇs. ɴᴏᴛʜɪɴɢ ᴄʜᴀɴɢᴇᴅ.",
            quote=True,
        )
        return

    # ── persist to disk (so changes survive a restart) ───────────────────
    persist_errors: list[str] = []
    pa_results: dict[str, bool] = {}
    ao_results: dict[str, bool] = {}
    try:
        pa_results = _patch_file(
            _PA_PATH,
            {"UPI_ID": new_upi, "SELLGRAM_API_KEY": new_key},
        )
    except Exception as e:
        persist_errors.append(f"premium_auto.py: {e}")
    try:
        ao_results = _patch_file(
            _AO_PATH,
            {"SELLGRAM_API_KEY": new_key},
        )
    except Exception as e:
        persist_errors.append(f"admin_orders.py: {e}")

    # ── monkey-patch in-memory (live, no restart needed) ─────────────────
    _pa.UPI_ID = new_upi
    _pa.SELLGRAM_API_KEY = new_key
    _ao.SELLGRAM_API_KEY = new_key

    # ── build status report ──────────────────────────────────────────────
    lines = ["<b>🔐 ᴄʀᴇᴅᴇɴᴛɪᴀʟs ʀᴏᴛᴀᴛᴇᴅ</b>", ""]

    if new_upi != old_upi:
        lines.append("<b>ᴜᴘɪ:</b>")
        lines.append(f"  ᴏʟᴅ → <code>{old_upi}</code>")
        lines.append(f"  ɴᴇᴡ → <code>{new_upi}</code>")
    if new_key != old_key:
        lines.append("<b>ᴀᴘɪ ᴋᴇʏ:</b>")
        lines.append(f"  ᴏʟᴅ → <code>{_mask_key(old_key)}</code>")
        lines.append(f"  ɴᴇᴡ → <code>{_mask_key(new_key)}</code>")

    lines.append("")
    lines.append("✅ ʟɪᴠᴇ ɪɴ-ᴍᴇᴍᴏʀʏ (ɴᴇxᴛ ᴘᴀʏᴍᴇɴᴛ ᴜsᴇs ɴᴇᴡ ᴠᴀʟᴜᴇs)")

    if persist_errors:
        lines.append("")
        lines.append("⚠️ <b>ᴘᴇʀsɪsᴛ ғᴀɪʟᴇᴅ — ɴᴇᴇᴅ ᴍᴀɴᴜᴀʟ ʀᴇsᴛᴀʀᴛ-ᴘʀᴏᴏғ ᴇᴅɪᴛ:</b>")
        for e in persist_errors:
            lines.append(f"  • <code>{e}</code>")
    else:
        ok_pa = all(pa_results.values())
        ok_ao = all(ao_results.values())
        if ok_pa and ok_ao:
            lines.append("✅ ᴘᴇʀsɪsᴛᴇᴅ ᴛᴏ ᴅɪsᴋ (sᴜʀᴠɪᴠᴇs ʙᴏᴛ ʀᴇsᴛᴀʀᴛ)")
        else:
            lines.append("⚠️ <b>ᴘᴀʀᴛɪᴀʟ ᴘᴇʀsɪsᴛ:</b>")
            lines.append(f"  • premium_auto.py: {pa_results}")
            lines.append(f"  • admin_orders.py: {ao_results}")
            lines.append("  ʀᴜɴ <code>/show_creds</code> ᴛᴏ ᴠᴇʀɪғʏ.")

    lines.append("")
    lines.append("ʀᴜɴ <code>/show_creds</code> ᴛᴏ ᴄᴏɴғɪʀᴍ.")

    await message.reply_text("\n".join(lines), quote=True)


# ═════════════════════════════════════════════════════════════════════════════
#  /show_creds
# ═════════════════════════════════════════════════════════════════════════════
@Bot.on_message(
    filters.command("show_creds") & filters.private & filters.user(OWNER_ID)
)
async def show_creds_cmd(client: Client, message: Message):
    cur_upi = getattr(_pa, "UPI_ID", "?")
    cur_key_pa = getattr(_pa, "SELLGRAM_API_KEY", "?")
    cur_key_ao = getattr(_ao, "SELLGRAM_API_KEY", "?")
    payee = getattr(_pa, "PAYEE_NAME", "?")

    sync = "✅ ɪɴ sʏɴᴄ" if cur_key_pa == cur_key_ao else "⚠️ ᴏᴜᴛ ᴏғ sʏɴᴄ"

    text = (
        "<b>🔐 ᴄᴜʀʀᴇɴᴛ ᴄʀᴇᴅᴇɴᴛɪᴀʟs</b>\n\n"
        f"<b>ᴜᴘɪ:</b> <code>{cur_upi}</code>\n"
        f"<b>ᴘᴀʏᴇᴇ:</b> <code>{payee}</code>\n\n"
        f"<b>ᴀᴘɪ ᴋᴇʏ (premium_auto):</b> <code>{_mask_key(cur_key_pa)}</code>\n"
        f"<b>ᴀᴘɪ ᴋᴇʏ (admin_orders):</b> <code>{_mask_key(cur_key_ao)}</code>\n"
        f"<b>sʏɴᴄ:</b> {sync}\n\n"
        "<i>ᴜsᴇ <code>/rotate_upi &lt;upi&gt; &lt;key&gt;</code> ᴛᴏ ᴄʜᴀɴɢᴇ.</i>"
    )
    await message.reply_text(text, quote=True)
