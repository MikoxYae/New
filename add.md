# 💎 Premium Plan Manager — `/psetting`

A button-driven panel for admins to define, list, delete, and grant
premium plans. Users can view active offers via `/plans`.

> Added in this update.

---

## 📋 Commands

| Command     | Who can use | What it does                                              |
|-------------|-------------|-----------------------------------------------------------|
| `/psetting` | Admin / Owner | Open the Premium Plan Manager (inline buttons)         |
| `/plans`    | Anyone        | Show all available premium plans (name, tier, price)   |

These are also added to `/commands` (admin help).

---

## 🛠 Panel Layout

When you run `/psetting` you'll see this menu:

```
💎 Premium Plan Manager
─────────────────────
[ 📋 List Plans ]   [ ➕ Add Plan ]
[ 🗑 Delete Plan ]  [ 🎁 Grant ]
[       ❌ Close       ]
```

| Button | Description |
|--------|-------------|
| 📋 **List Plans**   | Show every plan with its name, tier, price, duration and ID |
| ➕ **Add Plan**     | 4-step wizard to create a plan (name → tier → duration → price) |
| 🗑 **Delete Plan**  | Tap-to-delete list of all existing plans |
| 🎁 **Grant**        | Pick a plan, send a `user_id`, plan is applied + user is notified |
| ❌ **Close**        | Dismiss the panel |

---

## ➕ Adding a Plan (4 steps)

1. **Name** — type a free-form name. Examples: `Gold 1 Month`, `Starter`, `Yearly Platinum`.
2. **Tier** — pick a button: `🥇 Gold` or `💎 Platinum`.
3. **Duration value + unit** — type a positive number, then pick a unit:

   | Code | Meaning |
   |------|---------|
   | `Minutes` | minutes |
   | `Hours`   | hours |
   | `Days`    | days |
   | `Weeks`   | weeks (stored as 7 × value days when granting) |
   | `Months`  | months (~30 × value days when granting) |
   | `Years`   | years (365 × value days when granting) |

4. **Price** — any string you want shown to users. Examples: `₹49`, `$5`, `Free`, `Contact owner`.

After confirming, the plan is saved in MongoDB collection **`premium-plans`** and shown back with its generated ID.

---

## 🎁 Granting a Plan

1. Open `/psetting` → **🎁 Grant**.
2. Tap the plan you want to apply.
3. Send the target user's numeric `user_id`.

The bot will:

- Convert the plan's duration into a real expiry timestamp,
- Save the user as premium in the `premium-users` collection,
- DM the user a confirmation with the plan name + expiry time.

Equivalent to running `/addpremium <user_id> <value> <unit> <tier>` manually,
but driven entirely by inline buttons.

---

## 🧾 Where data is stored

Two MongoDB collections are used:

- **`premium-plans`** — plan templates created via `/psetting`
- **`premium-users`** — actual granted premium memberships (already existed)

Plans never auto-expire on their own — they're just templates.
Premium users still expire normally and are auto-cleaned by the existing scheduler.

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

If no plans are defined, the bot replies with:

```
No premium plans available yet.
```

---

## 🔐 Permissions

- `/psetting` — admins + owner only (uses the same `admin` filter as `/settings`).
- `/plans` — open to everyone in private chat.
- All callback buttons under `pst_*` re-check admin status, so a non-admin
  cannot use a forwarded button to mutate plans.

---

## 🧩 Files added / changed

| File | Change |
|------|--------|
| `database/db_plans.py`     | **New** — CRUD for the `premium-plans` collection |
| `plugins/psetting.py`      | **New** — `/psetting` command, callbacks, text wizard, `/plans` |
| `config.py`                | Added `/plans` and `/psetting` to `CMD_TXT` |
| `add.md`                   | **New** — this file |
| `README.md`                | Linked this doc from the features section |

No existing behaviour was modified.
