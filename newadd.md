# 🆕 Automatic Premium Flow — `newadd.md`

This document describes the **new automatic-premium purchase flow** that
replaces the previous manual Gold / Platinum screenshot-based flow.

---

## 1. What was removed

| File | Removed |
|------|---------|
| `plugins/cbb.py` | `UPI_ID`, `GOLD_PREMIUM_PRICES`, `PLATINUM_PREMIUM_PRICES`, `user_payment_info`, `generate_upi_qr()`, all callback branches for `premium`, `gold_premium`, `gold_*`, `platinum_premium`, `plat_*`, `payment_done`, and the `forward_payment_screenshot()` photo handler. |

The Gold/Platinum tier selection UI, manual screenshot upload, and
owner-runs-`/addpremium` workflow are **gone**. The new flow is fully
automatic via the Sellgram Paytm Status API.

> The MongoDB `premium-users` schema and `/addpremium`, `/remove_premium`,
> `/myplan`, `/premium_users`, expiry-monitor, etc. are **untouched** — the
> new flow simply calls `add_premium()` internally once the API confirms a
> payment, so existing premiums and owner commands keep working exactly
> as before.

---

## 2. What was added

### 2.1 New file — `plugins/premium_auto.py`

A self-contained plugin that:

1. Listens for the `Buy Premium` button press (callback `premium` /
   `buy_premium` — same callback already emitted by `start.py` when a user
   exhausts their free daily links, so **no change to start.py is required**).
2. Shows the new plan menu with 4 options:

   | Plan | Price |
   |------|-------|
   | 1 hour (test) | ₹1 |
   | 1 day  | ₹10 |
   | 7 days | ₹50 |
   | 30 days | ₹150 |

3. When a plan is picked, it generates a unique **order ID** (see §3),
   persists the order to MongoDB, and replies with a fresh QR-code image
   plus instructions and three buttons:

   * ✅ **I Have Paid** — `pa_paid_<order_id>`
   * 🆘 **Support**     — `https://t.me/Iam_addictive`
   * 🔒 **Close**        — `pa_close`

4. When the user clicks **I Have Paid**, the bot calls the Sellgram API:

   ```
   GET https://ptapi.sellgram.in/status/{order_id}?api_key=8Mv3zQgQZNVCdU4iBaAFvtu8
   ```

5. If the response is `data.status == "TXN_SUCCESS"` and the paid amount
   is ≥ the expected amount, the bot:
   * Calls `add_premium(user_id, time_value, time_unit, "gold")`
   * Marks the order as `paid` in `pending_orders`
   * Spawns `monitor_premium_expiry()` for auto-expiry reminders
   * Sends the user a green "Premium Activated" confirmation
   * Sends the owner a "💰 New premium sale" notification

6. If the API returns anything other than success, the bot replies with
   the raw status + message and tells the user to retry in a few seconds.
   The order stays `pending` so they can press **I Have Paid** again
   without losing it.

### 2.2 New MongoDB collection — `pending_orders`

| Field | Description |
|-------|-------------|
| `order_id` | The full order id (e.g. `0MIKO-150-5473072051-1777487452-7391`) |
| `user_id` | Telegram user id |
| `amount` | INR integer |
| `plan_id` | `1h` / `1d` / `7d` / `30d` |
| `time_value` | int (e.g. `30`) |
| `time_unit` | `h` or `d` |
| `status` | `pending` → `paid` |
| `created_at` | ISO timestamp |
| `txn_id` | Set on success |
| `paid_at` | Set on success |

> Persisting the order means a bot restart between QR-display and
> payment doesn't break the flow — the user can still press
> **I Have Paid** later and get auto-activated.

---

## 3. Order-ID format

Order ID **starts with `0`** (zero), as requested:

```
0MIKO-{amount}-{user_id}-{unix_ts}-{rand4}
```

Example: `0MIKO-30-5473072051-1777487452-7391`

| Segment | Meaning |
|---------|---------|
| `0`     | Required ZERO prefix |
| `MIKO`  | Bot brand prefix |
| `30`    | Plan amount in INR |
| `5473072051` | Telegram user id |
| `1777487452` | Unix timestamp of order creation |
| `7391`  | 4-digit random salt for uniqueness |

---

## 4. Trigger flow (when does the user see "Buy Premium"?)

This stays consistent with what `plugins/start.py` already does.
There are **two ways** the user reaches the buy-premium button:

### Case A — Shortener is **OFF** (or owner hasn't configured one)

After the user uses up their daily free-link quota
(`db.get_free_link_limit()` — default 5/day):

```
🔒 Your N free daily links have been used!
Daily limit reached. Come back tomorrow…
[ • ʙᴜʏ ᴘʀᴇᴍɪᴜᴍ • ]
```

### Case B — Shortener is **ON** + Free Link is set

After exhausting free links, the user gets an ad-token link
**plus** the buy-premium button:

```
🔒 Your N free daily links have been used!
Please refresh your token to continue…
[ • ᴏᴘᴇɴ ʟɪɴᴋ • ]   [ • ᴛᴜᴛᴏʀɪᴀʟ • ]
[ • ʙᴜʏ ᴘʀᴇᴍɪᴜᴍ • ]
```

In **both** cases, clicking **Buy Premium** routes to the new
`open_premium_menu()` callback in `plugins/premium_auto.py`.

---

## 5. Full state machine

```
[start.py: free-link limit hit]
        │
        ▼
[Buy Premium]  ─►  callback "premium" / "buy_premium"
        │
        ▼
[plugins/premium_auto.py :: open_premium_menu]
   shows plan menu (1h ₹1 | 1d ₹10 | 7d ₹50 | 30d ₹150)
        │
        ▼
[user picks plan]  ─►  callback "pa_plan_<id>"
        │
        ▼
[pick_plan]
   generates 0MIKO-… order id
   persists to pending_orders
   builds QR (UPI URL contains order_id in tn= and tr=)
   replies with QR image + instructions + buttons
        │
        ▼
[user pays via any UPI app, then taps "I Have Paid"]
        │
        ▼
[i_have_paid]  ─►  callback "pa_paid_<order_id>"
   GET https://ptapi.sellgram.in/status/<order_id>?api_key=…
        │
        ├── status = TXN_SUCCESS  +  amount ≥ expected
        │       │
        │       ▼
        │  add_premium(user_id, time_value, time_unit, "gold")
        │  monitor_premium_expiry() spawned
        │  pending_orders.status = "paid"
        │  user gets ✅ confirmation
        │  owner gets 💰 sale notification
        │
        └── anything else
                │
                ▼
           reply with the status + resp_msg
           order stays "pending" so user can retry
```

---

## 6. Configuration constants

All inside `plugins/premium_auto.py`:

```python
SELLGRAM_API_BASE = "https://ptapi.sellgram.in"
SELLGRAM_API_KEY  = "8Mv3zQgQZNVCdU4iBaAFvtu8"
UPI_ID            = "paytm.s20gmbu@pty"
PAYEE_NAME        = "MikoPremium"
SUPPORT_URL       = "https://t.me/Iam_addictive"

PLANS = {
    "1h":  ("1 hour (test)", 1,   1,  "h"),
    "1d":  ("1 day",         10,  1,  "d"),
    "7d":  ("7 days",        50,  7,  "d"),
    "30d": ("30 days",       150, 30, "d"),
}
```

> The UPI ID is **embedded only inside the QR code** — it is **not**
> printed in any caption or instruction text, exactly as requested.

---

## 7. Tier granted

Every successful auto-purchase activates the **`gold`** tier of the
existing premium system. That gives the user:

* Token bypass (no shortener required)
* Free-link-limit bypass (unlimited daily links)
* Protect-content bypass (save & forward freely)

If you later want plan-specific tier (e.g. `30d` → platinum), change the
last argument of `add_premium(...)` in `plugins/premium_auto.py:i_have_paid`.

---

## 8. Files in this branch

| File | State |
|------|-------|
| `plugins/premium_auto.py` | **NEW** — handles entire purchase + verify + activate flow |
| `plugins/cbb.py` | **MODIFIED** — old buy-premium UI + screenshot forwarder removed |
| `newadd.md` | **NEW** — this document |

No other files were touched. Existing dependencies in
`requirements.txt` already cover everything needed (`aiohttp`, `qrcode[pil]`,
`Pillow`, `motor`).

---

## 9. Hotfix log

### v1.7 — UPI / Sellgram credentials rotation

**Files touched:** `plugins/premium_auto.py`, `plugins/admin_orders.py`,
`README.md`, `newadd.md`

#### 9.7.1 What changed

Switched the live UPI receiver and the Sellgram Paytm Status API key to
new values supplied by the owner:

| Setting | Old | New |
|---|---|---|
| `UPI_ID` | `paytm.s191ecw@pty` | `paytm.s20gmbu@pty` |
| `SELLGRAM_API_KEY` | `YAw9KGJTEg6nB5frTWK_mqQc` | `8Mv3zQgQZNVCdU4iBaAFvtu8` |

#### 9.7.2 Where these are used

- `plugins/premium_auto.py` — generates the `upi://pay?...` deep-link
  + QR for the **Buy Premium** flow, and verifies payments by polling
  `https://ptapi.sellgram.in/status/{order_id}?api_key=...`.
- `plugins/admin_orders.py` — uses the same key for `/checkorder` and
  `/forceverify` so admin recovery flows hit the same Sellgram account.

Both files keep their constants in sync (independent declarations, no
cross-import) so a future swap means editing both — README documents
this clearly.

#### 9.7.3 Backward compatibility

- Order-ID format **unchanged** (`ZERO-{amount}-{user_id}-{ts}-{HEX4}`).
- Plans, prices and durations **unchanged** (`1h₹1`, `1d₹10`, `7d₹50`,
  `30d₹150`).
- Existing premium users are not affected — only new payments route
  to the new UPI handle and are verified against the new key.

#### 9.7.4 Rotation checklist (for future swaps)

1. Edit `SELLGRAM_API_KEY` in **both** `plugins/premium_auto.py` and
   `plugins/admin_orders.py`.
2. Edit `UPI_ID` in `plugins/premium_auto.py`.
3. Restart the bot (`python3 main.py`).
4. Test: open `/start` → **Buy Premium** → 1 ʜᴏᴜʀ ₹1, scan the QR,
   confirm the payee VPA matches the new UPI, pay ₹1 from another
   account, click **✅ I Have Paid**, expect the receipt + invite link.
5. Run `/checkorder ZERO-1-<uid>-<ts>-<hex>` to confirm the admin
   panel sees the same record.

---

### v1.6 — new `/help` command (button-driven, paginated)

**File added:** `plugins/help_cmd.py`

#### 9.6.1 Why a new file

The old "help" was a callback inside `cbb.py` that just rendered the
empty `HELP_TXT` constant. With the v1.2 admin-orders panel and v1.5
batch fixes there are now ~25 commands across the bot — far too many
for a single message under Telegram's 4096-char text limit. The new
`/help` is a fully button-driven menu so we can keep every page short,
readable, and easy to edit in one file.

`cbb.py` is **not touched** — its old `help` callback (triggered from
the `/start` screen's "ʜᴇʟᴘ" button) keeps working. The new system uses
its own callback prefix `hlp_*` so there is zero collision.

#### 9.6.2 Layout

```
/help
 ├─ 👤 USER COMMANDS                  →  hlp_user
 ├─ ⚙️ OWNER COMMANDS  (owner only)   →  hlp_owner
 │     ├─ 📋 Admin Orders             →  hlp_o_orders
 │     ├─ 💎 Premium Mgmt             →  hlp_o_prem
 │     ├─ 🔗 Link Gen                 →  hlp_o_link
 │     ├─ 📢 Broadcasts               →  hlp_o_bc
 │     └─ 📊 Stats & Settings         →  hlp_o_stat
 ├─ 📞 SUPPORT  (url → t.me/{OWNER})
 └─ ❌ CLOSE                          →  hlp_close (deletes the menu)
```

Every sub-page has 🔙 BACK and ❌ CLOSE.

#### 9.6.3 Coverage

| Section | Commands documented |
|---|---|
| 👤 User           | `/start`, `/help`, `/myplan`, premium-buy flow |
| 📋 Admin Orders   | `/id`, `/ord`, `/amount`, `/stats`, `/checkorder`, `/forceverify` |
| 💎 Premium Mgmt   | `/addpremium`, `/remove_premium`, `/premium_users`, `/start_premium_monitoring` |
| 🔗 Link Gen       | `/genlink`, `/batch`, `/custom_batch`, direct upload |
| 📢 Broadcasts     | `/broadcast`, `/pbroadcast`, `/dbroadcast` |
| 📊 Stats & Settings | `/settings`, `/peakhours`, `/weeklyreport`, `/cleanstats`, `/commands` |

Every command entry includes:
- The exact syntax with `<placeholder>` arguments
- A short description of what it does
- One or more concrete `<i>ᴇxᴀᴍᴘʟᴇ:</i>` lines

#### 9.6.4 Owner-only safety

The OWNER COMMANDS button is hidden for normal users (the keyboard is
built dynamically based on `await _is_owner_or_admin(uid)` which checks
`OWNER_ID` first then `db.admin_exist(uid)`). Even if a user crafts a
`hlp_owner` callback by hand, the callback router re-checks ownership
and answers `"Owner-only."` instead of rendering the page.

#### 9.6.5 Robustness

- `_safe_edit()` handles the case where the user opened `/help` on a
  message that's a photo/caption — it edits if possible, otherwise
  deletes and re-sends fresh.
- All `query.answer()` and `delete()` calls are wrapped in try/except
  so a rate-limit or stale callback never crashes the handler.
- No new env-vars. SUPPORT button uses the existing `OWNER` username
  from `config.py` (`t.me/{OWNER}`).

---

### v1.5 — `/custom_batch`: double-copy + STOP-junk-link bug fix

**File touched:** `plugins/channel_post.py`

#### 9.5.1 Bugs reported by user

1. **Every media sent during `/custom_batch` was being copied to the DB
   channel TWICE.**
2. **Pressing STOP generated the proper batch link but ALSO an extra
   junk encoded share-link for the literal text `"STOP"`.**

#### 9.5.2 Root cause

`/custom_batch` was using `client.ask` (pyromod) to wait for each
incoming message. `client.ask` returns the message to the awaiting
coroutine **but does not stop it from also reaching the regular
`@Bot.on_message` handlers**. So every media:

1. was returned by `client.ask` → custom_batch copied it to the DB
   channel (1st copy)
2. ALSO continued to the catch-all `channel_post` handler → which
   copied it AGAIN and replied with a share-link (2nd copy + junk
   reply)

The `not_in_batch` filter on `channel_post` was supposed to block this,
but the discard of the user-id from `_in_custom_batch` ran inside
`finally` and could happen before the STOP message's filter check,
creating a race that let STOP slip through and produce its own junk
encoded link.

#### 9.5.3 Fix — high-priority capture handler + per-user queue

A new handler is registered in **group `-5`** (i.e. before the default
group `0` where `channel_post` lives):

```python
@Bot.on_message(filters.private & admin & in_batch, group=-5)
async def _capture_batch_messages(client, message):
    q = _batch_queues.get(message.from_user.id)
    if q is not None:
        q.put_nowait(message)
    raise StopPropagation
```

It pushes the incoming message into a per-user `asyncio.Queue` and then
raises `StopPropagation`, which means **no later-group handler (including
`channel_post`) can ever see the same message a second time.**

`/custom_batch` no longer uses `client.ask`; instead it pulls from the
queue:

```python
q = asyncio.Queue()
_batch_queues[uid] = q
_in_custom_batch.add(uid)
...
user_msg = await asyncio.wait_for(q.get(), timeout=300)
if user_msg.text and user_msg.text.strip().upper() == "STOP":
    break  # never copy STOP to db_channel
```

Result:

- Each media is copied **exactly once**.
- STOP is consumed by the queue, recognised in the loop, breaks out,
  and is **never** forwarded to `channel_post`. No junk link.
- Idle session is auto-ended after 5 min of inactivity (was 60 s
  before; bumped because batches can take longer).
- `FloodWait` on the `.copy()` call now retries once instead of
  failing the message silently.

#### 9.5.4 Side effects / no regressions

- `/batch` and `/genlink` still use `client.ask` (they only collect
  forwarded refs, not real media — no double-copy risk).
- Outside `/custom_batch`, the new capture handler is inert because
  the `in_batch` filter requires the user to be in `_in_custom_batch`.
- `channel_post`, `/id`, `/ord`, `/amount`, `/stats`, `/checkorder`,
  `/forceverify` continue to behave as before.

---

### v1.4 — channel_post: missing-exclusion bug fix + small polish

**File touched:** `plugins/channel_post.py`

> Note: an earlier draft of v1.4 also added an Auto-Delete (DD) filter
> to channel-post replies. That feature was **reverted on user request**
> in v1.4.1 — see below. v1.4 is now bug-fix + polish only.

#### 9.4.1 BUG FIX — admin commands were being swallowed

The catch-all handler in `channel_post.py` listens to *every* private
admin message that is **not** in its excluded-commands list, copies it
into the DB channel, and replies with a share-link. Its exclusion list
was last updated long before v1.2 and was missing the new admin
commands:

| Command | Was it excluded? |
|---|---|
| `/id`           | ❌ no |
| `/ord`          | ❌ no |
| `/amount`       | ❌ no |
| `/stats`        | ❌ no |
| `/checkorder`   | ❌ no |
| `/forceverify`  | ❌ no |

Result: every time the owner typed e.g. `/id today`, two things
happened:

1. The admin-orders handler answered correctly with the orders list.
2. The channel_post handler **also** ran, copied the literal text
   "`/id today`" into the DB channel as a "file", and replied with a
   junk share-link.

**Fix:** all six commands are now in the `_EXCLUDED_COMMANDS` list, plus
`help` and `about` (which were also missing). The exclusion list is now
named and centralised at the top of the file.

#### 9.4.2 Other minor polish in `channel_post.py`

- The previously-defined-but-unused `not_in_batch` filter is now wired
  into the catch-all handler, so the in-progress `/custom_batch` lock
  is enforced at the filter layer (cleaner than the runtime check).
- `disable_web_page_preview=True` added to `/batch`, `/genlink`, and
  `/custom_batch` link replies so the Telegram link-preview no longer
  clutters the chat.
- Bare `except:` in `client.ask` blocks tightened to `except Exception:`.

#### 9.4.3 v1.4.1 — Auto-Delete (DD) filter REVERTED on user request

The Auto-Delete (DD) timer integration that was added in the first push
of v1.4 (link replies + admin upload auto-deleting after the global
`db.get_del_timer()` value) was rolled back. Reasoning from the user:
they did not want channel-post link replies tied to the same global
Auto-Delete timer that controls user-side file delivery in `start.py`.

Specifically the following were removed from `channel_post.py`:

- import of `database.database.db` and `helper_func.get_exp_time`
- the `_autodel_after(delay, *messages)` helper
- the `_autodel_suffix(seconds)` helper
- the `_get_autodel_timer()` helper
- all `auto_del = await _get_autodel_timer()` lookups in
  `channel_post`, `batch`, `link_generator`, `custom_batch`
- all `asyncio.create_task(_autodel_after(...))` schedules
- the inline `⏱ ᴀᴜᴛᴏ-ᴄʟᴇᴀɴ:` notice appended to link replies

The 9.4.1 exclusion-list bug fix and the 9.4.2 polish (wired
`not_in_batch`, `disable_web_page_preview=True`, tightened excepts)
remain — they are unrelated to auto-delete.

`start.py`'s own Auto-Delete behaviour for delivered files is
**unchanged** and continues to work as before.

---

### v1.3 — order-id prefix renamed to `ZERO-`

`_gen_order_id` now emits `ZERO-…` instead of `MIKO-…`:

```
ZERO-{amount}-{user_id}-{unix_ts}-{rand4_HEX}
```

Example: `ZERO-1-7137144805-1777510697-A1F4`

Old orders (`0MIKO-…` from v1.0 and `MIKO-…` from v1.2) already saved in
MongoDB still verify normally — every lookup is by the exact `order_id`
field, never by prefix. Only **new** orders created from now on use
`ZERO-`.

---

### v1.2 — admin-side orders panel + order-id polish

#### 9.2.1 Order ID change

**v1.0 → v1.2:** prefix went from `0MIKO-` to `MIKO-`, and the random
suffix switched from 4 digits to 4 uppercase HEX chars.
**v1.3:** prefix is now `ZERO-` (see above).

```python
def _gen_order_id(amount, user_id):
    ts = int(time.time())
    rand = "".join(random.choices("0123456789ABCDEF", k=4))
    return f"ZERO-{amount}-{user_id}-{ts}-{rand}"
```

#### 9.2.2 New file: `plugins/admin_orders.py`

A self-contained admin panel that reads the `pending_orders` Mongo
collection (filled by `premium_auto.py`) and ships **6 owner-only
commands**. All commands are gated by `filters.user(OWNER_ID)` —
non-owners get nothing.

##### 📊 Reporting commands

| Command | What it does |
|---|---|
| `/id [date]` | Paginated successful-orders feed for the date (default = today). 10 per page. Header shows total count + total ₹ + page indicator. Each row shows: `MIKO-…` order id, user id, plan label (Gold 1ʜ / 1ᴅ / 7ᴅ / 30ᴅ), amount, IST time, and the bank TXN id. Buttons: **◀️ ᴘʀᴇᴠ / page / ɴᴇxᴛ ▶️**, **📄 ᴇxᴘᴏʀᴛ ᴀʟʟ**, **💰 ᴀᴍᴏᴜɴᴛ**, **🔄 ʀᴇғʀᴇsʜ**, **✖️ ᴄʟᴏsᴇ**. |
| `/ord [date]` | Plain serial-wise list of just the order IDs (`1. MIKO-…`). Auto-falls-back to a `.txt` document if the list goes over 4000 chars. |
| `/amount [date]` | Per-plan income breakdown: `1ʜ × N = ₹X`, `1ᴅ × N = ₹X`, `7ᴅ × N = ₹X`, `30ᴅ × N = ₹X`, plus Gold total + Grand total + order count. Buttons: **📋 ᴏʀᴅᴇʀ ɪᴅs**, **✖️ ᴄʟᴏsᴇ**. |
| `/stats` | One-screen lifetime dashboard: total orders, total revenue, active premium users (distinct user ids that ever paid), top-selling plan (plan + price + count), and best-performing day (IST date + revenue). |

`[date]` accepts:

- *(omitted)* → today (IST)
- `today`
- `yesterday`
- `DD-MM-YYYY` / `DD/MM/YYYY` / `YYYY-MM-DD` / `DD-MM-YY`

##### 💸 Payments & recovery

| Command | What it does |
|---|---|
| `/checkorder <order_id>` | Read-only debug. Looks up the order in our DB **and** queries Sellgram `/status/<order_id>`, prints both side-by-side. If DB says `pending` but Sellgram says `TXN_SUCCESS`, prints a `⚠️ ᴍɪsᴍᴀᴛᴄʜ` hint suggesting `/forceverify`. |
| `/forceverify <order_id>` | Recovery command. When Sellgram confirms `TXN_SUCCESS` and the amount matches but our DB still says `pending` (e.g. user closed the chat before tapping *I have paid*), this re-checks, promotes the order to `paid`, calls `add_premium(...)`, spawns the expiry monitor, sends the user the standard **receipt** (order id, amount, duration, expiry), and the order then shows up in `/id`, `/ord`, and `/amount`. Idempotent — already-paid orders short-circuit with an `ℹ️ ᴀʟʀᴇᴀᴅʏ ᴘᴀɪᴅ` reply. |

##### Mongo schema queried

`pending_orders` (already created by `premium_auto.py`):

```jsonc
{
  "order_id":   "MIKO-150-5473072051-1777487452-A2F1",
  "user_id":    5473072051,
  "amount":     150,
  "plan_id":    "30d",       // one of: 1h, 1d, 7d, 30d
  "time_value": 30,
  "time_unit":  "d",
  "status":     "paid",      // or "pending"
  "created_at": "2026-04-30T00:01:32.123456",
  "paid_at":    "2026-04-30T00:02:48.456789",
  "txn_id":     "2026043011091000025639071124752288",
  "force_verified": true     // only present when /forceverify reconciled it
}
```

Date filtering converts IST day boundaries to **naive UTC ISO strings**
(matching how `paid_at` is stored via `datetime.utcnow().isoformat()`)
and uses a Mongo range query `{"$gte": start, "$lt": end}`, so it stays
fast even on large collections.

##### Callback router

| `callback_data` regex | Action |
|---|---|
| `aord_id_<YYYYMMDD>_<page>` | Re-render `/id` page |
| `aord_amt_<YYYYMMDD>`        | Render `/amount` for date |
| `aord_exp_<YYYYMMDD>`        | Build `.txt` and reply as document |
| `aord_close`                 | Delete message |
| `aord_noop`                  | Pagination indicator (no-op) |

All callbacks re-validate `query.from_user.id == OWNER_ID`, so even if
a button leaks, only the owner can actuate it.

##### Files touched in v1.2

| File | Change |
|---|---|
| `plugins/admin_orders.py` | **New** — full admin panel (~430 lines). |
| `plugins/premium_auto.py` | Order-ID generator: dropped leading `0`, switched random suffix to uppercase HEX. |
| `newadd.md`               | This section. |

---

### v1.1 — config import fix

**Problem:** First push imported `DATABASE_URL` and `DATABASE_NAME` from
`config.py`, but the project actually exports those values under the
constant names **`DB_URI`** and **`DB_NAME`** (the `DATABASE_URL` /
`DATABASE_NAME` strings are only the env-var keys read inside `config.py`).
Result: the bot crashed at startup with

```
ImportError: cannot import name 'DATABASE_URL' from 'config'
```

**Fix:** `plugins/premium_auto.py` now imports the correct names:

```python
from config import DB_URI, DB_NAME, OWNER_ID, PREMIUM_PIC
…
_mongo = AsyncIOMotorClient(DB_URI)
_db    = _mongo[DB_NAME]
_orders_col = _db["pending_orders"]
```

After pulling this fix, `python3 main.py` starts cleanly.

---

## 10. Quick smoke test (1₹ flow)

1. Set the free-link limit to a low number from `/settings → Free Link`.
2. From a non-admin account, hit `/start <link>` repeatedly until the
   "free links exhausted" message appears.
3. Tap **Buy Premium** → tap **1ʜ — ₹1 (ᴛᴇsᴛ)**.
4. Pay ₹1 via any UPI app to the QR shown.
5. After ~10 s, tap **I Have Paid**.
6. Bot should reply with **✅ Payment verified — premium activated!**
   and the user gets 1 hour of gold premium.
