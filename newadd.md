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
   GET https://ptapi.sellgram.in/status/{order_id}?api_key=YAw9KGJTEg6nB5frTWK_mqQc
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
SELLGRAM_API_KEY  = "YAw9KGJTEg6nB5frTWK_mqQc"
UPI_ID            = "paytm.s191ecw@pty"
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

### v1.2 — admin-side orders panel + order-id polish

#### 9.2.1 Order ID change

**Before:** `0MIKO-1-7137144805-1777510697-0104` — leading `0`, last 4 chars
were digits only.
**Now:**   `MIKO-1-7137144805-1777510697-A1F4` — no leading `0`, last 4
chars are uppercase HEX. Format:

```
MIKO-{amount}-{user_id}-{unix_ts}-{rand4_HEX}
```

Generator (`plugins/premium_auto.py → _gen_order_id`):

```python
def _gen_order_id(amount, user_id):
    ts = int(time.time())
    rand = "".join(random.choices("0123456789ABCDEF", k=4))
    return f"MIKO-{amount}-{user_id}-{ts}-{rand}"
```

Old `0MIKO-…` orders already in MongoDB still verify normally — lookup
is by `order_id` field, not by prefix.

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
