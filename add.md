# 💎 Premium Plan Manager — `/psetting`

A button-driven panel for admins to define, list, delete, grant
premium plans, **and now attach a Telegram channel to a plan as a
gift** that buyers are auto-added to and auto-kicked from on expiry.
Users can view active offers via `/plans`.

---

## 📋 Commands

| Command     | Who can use   | What it does                                         |
|-------------|---------------|------------------------------------------------------|
| `/psetting` | Admin / Owner | Open the Premium Plan Manager (inline buttons)      |
| `/plans`    | Anyone        | Show all available premium plans (name, tier, price)|

These are also added to `/commands` (admin help).

---

## 🛠 Panel Layout

When you run `/psetting` you'll see this menu:

```
💎 Premium Plan Manager
─────────────────────
[ 📋 List Plans ]   [ ➕ Add Plan ]
[ 🗑 Delete Plan ]  [ 🎁 Grant ]
[ 🎀 Gift Channel ]
[       ❌ Close       ]
```

| Button | Description |
|--------|-------------|
| 📋 **List Plans**   | Show every plan with its name, tier, price, duration, ID and gift channel (if any) |
| ➕ **Add Plan**     | 4-step wizard to create a plan (name → tier → duration → price) |
| 🗑 **Delete Plan**  | Tap-to-delete list of all existing plans |
| 🎁 **Grant**        | Pick a plan, send a `user_id`, plan is applied + user is notified |
| 🎀 **Gift Channel** | Attach a Telegram channel to a plan; buyers are auto-added on payment, auto-kicked on expiry |
| ❌ **Close**        | Dismiss the panel |

---

## ➕ Adding a Plan (4 steps)

1. **Name** — type a free-form name. Examples: `Gold 1 Month`, `Starter`, `Yearly Platinum`.
2. **Tier** — pick a button: `🥇 Gold` or `💎 Platinum`.
3. **Duration value + unit** — type a positive number, then pick a unit
   (`Minutes / Hours / Days / Weeks / Months / Years`).
4. **Price** — any string you want shown to users. Examples: `₹49`, `$5`, `Free`.

After confirming, the plan is saved in MongoDB collection **`premium-plans`** and shown back with its generated ID.

---

## 🎁 Granting a Plan

1. Open `/psetting` → **🎁 Grant**.
2. Tap the plan you want to apply.
3. Send the target user's numeric `user_id`.

The bot saves the user as premium, DMs them a confirmation with the
plan name + expiry, and equivalent to running
`/addpremium <user_id> <value> <unit> <tier>` manually.

---

## 🎀 Gift Channel — full flow

The Gift Channel feature lets you attach **any** Telegram channel
(public or private) to a premium plan. From that point on, every
buyer of that plan is automatically invited to the channel after
payment and removed from it the moment their premium expires.

### One-time setup (admin)

1. Add this **bot as an administrator** in your channel.
   It must have at least:
   - **Invite Users via Link** ✅
   - **Ban Users** ✅ (so it can remove members on expiry)
2. Run `/psetting` → tap **🎀 Gift Channel**.
3. Tap the plan you want to attach a channel to.
   (Plans already linked show a small **✓** next to their name.)
4. Send the channel ID — it must start with `-100` (e.g. `-1001234567890`).
5. The same message edits in place to **Verifying…**, then to:
   - ✅ **Linked** — the channel title + ID is now stored on that plan, **or**
   - ❌ **Verification Failed** — bot is not admin / lacks invite permission /
     ID is wrong. A **🔁 Try again** button is shown.

To remove an existing link: open the plan in the Gift menu and tap
**🗑 Remove existing link**.

### What buyers see

When a user opens **Buy Premium** and picks a plan that has a gift
channel attached, the QR caption now contains an extra line:

```
🎀 ɢɪғᴛ ᴀᴅᴅᴇᴅ: <channel title>
(ʏᴏᴜ ᴡɪʟʟ ʙᴇ ɪɴᴠɪᴛᴇᴅ ᴀғᴛᴇʀ ᴘᴀʏᴍᴇɴᴛ)
```

After their payment is verified, **a second message** is sent to them:

```
🎀 ʏᴏᴜʀ ɢɪғᴛ ᴄʜᴀɴɴᴇʟ ɪs ʀᴇᴀᴅʏ

ᴄʜᴀɴɴᴇʟ: <channel title>

ʜᴏᴡ ᴛᴏ ᴊᴏɪɴ:
1. ᴛᴀᴘ ᴏᴘᴇɴ ᴄʜᴀɴɴᴇʟ ʙᴇʟᴏᴡ.
2. ᴛᴀᴘ ʀᴇǫᴜᴇsᴛ ᴛᴏ ᴊᴏɪɴ ɪɴ ᴛᴇʟᴇɢʀᴀᴍ.
3. ᴄᴏᴍᴇ ʙᴀᴄᴋ ʜᴇʀᴇ ᴀɴᴅ ᴛᴀᴘ ᴅᴏɴᴇ.

[ 📨 ᴏᴘᴇɴ ᴄʜᴀɴɴᴇʟ ]
[ ✅ ᴅᴏɴᴇ — ᴀᴅᴅ ᴍᴇ ]
```

The Open Channel button opens an invite link generated on-the-fly
with `creates_join_request=True`. When the user comes back and taps
**Done**, the bot calls `approve_chat_join_request` for that user
and edits the message to **🎀 ɢɪғᴛ ᴄʜᴀɴɴᴇʟ — ᴀᴅᴅᴇᴅ!**.

If the user taps Done before requesting to join, an alert tells
them: *"Open the channel and tap Request to Join first, then press
Done."*

### Auto-removal on expiry

The premium expiry monitor (`monitor_premium_expiry`) was extended:

- The moment a user's premium expires, the bot looks up every
  active gift grant for that user.
- For each linked channel, the bot performs `ban_chat_member` →
  short pause → `unban_chat_member`. This kicks the user but
  leaves the channel re-joinable if they buy the plan again later.
- Each grant is then marked `revoked` in `gift_grants`.
- The expiry DM the user receives gets an extra line:
  `🎀 ɢɪғᴛ ᴄʜᴀɴɴᴇʟ(s) ʀᴇᴍᴏᴠᴇᴅ: <count>`.

The same revocation also runs when an admin uses
`/remove_premium <user_id>` manually.

---

## 🧾 Where data is stored

Three MongoDB collections are used:

- **`premium-plans`** — plan templates created via `/psetting`.
  Now optionally carries `gift_channel_id` + `gift_channel_title`.
- **`premium-users`** — actual granted premium memberships (existed before).
- **`gift_grants`** — *new* — one document per (user, channel, plan)
  grant. Schema:
  ```
  user_id, channel_id, channel_title, plan_id,
  order_id, granted_at, expires_at, status
  ```
  `status` is `active` until the user is kicked, then `revoked`.

The `pending_orders` collection (used by the auto-payment flow) also
now carries `gift_channel_id` + `gift_channel_title` on orders for
plans that have a gift attached, so the post-payment delivery step
can run without re-reading the plan.

---

## 👤 What users see — `/plans`

```
💎 Available Premium Plans
─────────────────────

🥇 Gold 1 Month  (Gold)
   💰 Price: ₹49
   ⏳ Duration: 1 Months

💎 Platinum Yearly  (Platinum)
   💰 Price: ₹499
   ⏳ Duration: 1 Years

Contact the owner to purchase a plan.
```

If no plans are defined, the bot replies with: `No premium plans available yet.`

---

## 🔐 Permissions

- `/psetting` — admins + owner only (uses the same `admin` filter as `/settings`).
- `/plans` — open to everyone in private chat.
- All callback buttons under `pst_*` re-check admin status, so a non-admin
  cannot use a forwarded button to mutate plans.
- The gift-channel verification step requires the bot itself to be admin
  in the target channel; without `can_invite_users`, the link refuses to save.
- The `pa_giftdone_<order_id>` callback verifies the requesting user owns
  the order before approving any join request.

---

## 🧩 Files added / changed

| File | Change |
|------|--------|
| `database/db_plans.py`   | + `gifts_col` collection, `set_gift_channel`, `clear_gift_channel`, `grant_gift`, `list_active_gifts_for_user`, `mark_gift_revoked`, `revoke_user_gifts` |
| `plugins/psetting.py`    | + 🎀 Gift Channel button, plan-picker, channel-id input wizard with bot-admin verification, remove-link option |
| `plugins/premium_auto.py`| Captures `gift_channel_id/title` into `pending_orders`, shows `🎀 ɢɪғᴛ ᴀᴅᴅᴇᴅ` on QR caption, sends Open-Channel + Done message after payment, new `pa_giftdone_*` callback that approves join requests |
| `plugins/premium_cdm.py` | Imports `revoke_user_gifts`; both `monitor_premium_expiry` (auto) and `/remove_premium` (manual) now kick the user from every gift channel they currently hold a grant for |
| `add.md`                 | This file — extended with the Gift Channel section |

No existing behaviour was removed; everything described in the previous
revision of `add.md` still works exactly as before.

---

## 🧾 v1.11 Update — Detailed Receipt + QR Auto-Delete

After a buyer presses **✅ ɪ ʜᴀᴠᴇ ᴘᴀɪᴅ** and Sellgram confirms
`TXN_SUCCESS`, the bot now:

1. **Deletes the QR / instructions photo** so the user no longer sees
   the stale "complete your payment" card.
2. **Sends a detailed receipt** containing:
   👤 User Name · 🆔 User ID · 💎 Plan Type · 💰 Plan Amount ·
   📦 Order ID · 🔖 Txn ID · 📅 Active Date (IST) · ⏳ Expire Date (IST).

This is fully compatible with the **Gift Channel** flow described
above — the receipt is sent first, then the **🎀 Open Channel / ✅ Done**
card appears underneath. Nothing in `/psetting`, `grant_gift`, or
the expiry-kick path was changed.

See `newadd.md` → "v1.11 — Auto-Delete QR + Detailed Payment Receipt"
for the full technical writeup and the visual reference saved at
[`docs/v1.11_qr_expired_reference.jpg`](docs/v1.11_qr_expired_reference.jpg).
