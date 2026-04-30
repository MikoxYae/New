<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif">

  <h2 align="center">
      ──「ᴍɪᴋᴏ ᴀᴅᴠᴀɴᴄᴇ ғɪʟᴇ sʜᴀʀɪɴɢ ʙᴏᴛ」──
  </h2>

  <p align="center">
    <img src="https://i.imgur.com/PXphMya.jpeg">
  </p>

  <img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif">

  <details><summary><b>📌 ғᴇᴀᴛᴜʀᴇs :</b></summary>

  <b>🚀 Core Features:</b>

  • <b>Batch & Custom Batch Links:</b> Create links for one or multiple posts easily using `/batch` & `/custom_batch`
  • <b>Link Generator:</b> Instantly generate direct links with `/genlink`
  • <b>Broadcast Tools:</b> Send messages or media to all users using `/broadcast`, `/dbroadcast`, or `/pbroadcast`
  • <b>Auto File Deletion:</b> Control auto-delete timer with configurable duration
  • <b>User Management:</b> Ban/unban users and view banlist via `/ban`, `/unban`, `/banlist`
  • <b>Multi Force Subscription:</b> Add, delete, and manage multiple Force Sub channels
  • <b>Admin Control:</b> Add or remove admins with `/add_admin`, `/deladmin`, view list via `/admins`

  <b>🆓 Free Link System:</b>

  • <b>Daily Free Links:</b> Every user gets N free file links per day (default 5, configurable from Settings)
  • <b>After Free Limit:</b> User is prompted to buy Premium for unlimited access
  • <b>Bypass:</b> Admins, Owner, and Premium users skip the daily limit entirely
  • <b>Auto Reset:</b> Daily count resets automatically — no cron job needed
  • <b>Presets:</b> 5 / 10 / 15 / 20 / Custom — configurable from Settings panel

  <b>💎 Premium System (Auto UPI Verification):</b>

  | Plan | Price | Duration |
  |------|:---:|:---:|
  | ⏱️ Test     | ₹1   | 1 hour  |
  | 📅 Daily    | ₹10  | 1 day   |
  | 📆 Weekly   | ₹50  | 7 days  |
  | 🗓️ Monthly | ₹150 | 30 days |

  • <b>One-tap UPI checkout</b> — bot auto-builds a `upi://pay` deep-link + QR with a unique `ZERO-{amount}-{user_id}-{ts}-{HEX4}` order ID
  • <b>Sellgram Paytm Status API</b> verifies the transaction in real-time — no manual approval, no screenshot uploads
  • <b>Auto receipt + invite link</b> the moment the payment lands
  • <b>Auto expiry notification</b> — 24h + 1h reminders before plan ends
  • <b>Auto removal</b> when premium expires — `/start_premium_monitoring` runs the background job
  • <b>`/myplan`</b> — any user can check their plan and time remaining
  • <b>Manual override:</b> `/addpremium <user_id> <duration>` (e.g. `/addpremium 7137144805 30d`), `/remove_premium <user_id>`, `/premium_users`
  • <b>Recovery:</b> `/checkorder <order_id>` (read-only debug) and `/forceverify <order_id>` (re-runs Sellgram check + activates premium when API succeeded but DB lagged)
  • <b>Reporting:</b> `/id [today|yesterday|DD-MM-YYYY]`, `/ord <user_id>`, `/amount [today|yesterday|DD-MM-YYYY]`, `/stats`
  • <b>UPI / API key</b> live as constants in `plugins/premium_auto.py` (and mirrored in `plugins/admin_orders.py`) — see `newadd.md` for the rotation checklist

  <b>🛡️ Flood Protection:</b>

  • Per-user rate limiting — blocks users who spam messages too fast
  • Configurable limits via `FLOOD_LIMIT`, `FLOOD_WINDOW`, `FLOOD_BLOCK_DURATION` env vars
  • Auto warning + auto-delete of warning after block expires

  <b>📊 Activity Analytics:</b>

  • Peak hours tracker — see which hours your bot is most active
  • Weekly report — daily breakdown of activity over last 7 days
  • All data stored in MongoDB, auto-cleanup after 30 days

  <b>🔧 Bot Settings Panel:</b>

  • Maintenance mode — block all non-admin users instantly
  • Toggle protect content from `/settings`
  • <b>Free Link panel</b> — set daily free link limit (5/10/15/20/Custom)

  <b>💎 Premium Plan Manager (`/psetting`):</b>

  • Button-driven admin panel — add / list / delete premium plans
  • Each plan: name, tier (silver/gold/diamond), duration (days), price
  • Quick **Grant Plan** flow — pick a plan, give it to any user by ID
  • Users see live plans with `/plans` command
  • Full guide: see [`add.md`](./add.md)

  <b>✨ More features & enhancements coming soon...</b>
  </details>

  <img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif">

  <details><summary><b>⚙️ ᴠᴀʀɪᴀʙʟᴇs :</b></summary>

  ## Required Variables

  | Variable | Description |
  |----------|-------------|
  | `TG_BOT_TOKEN` | Your bot token from @BotFather |
  | `APP_ID` | Your API ID from my.telegram.org |
  | `API_HASH` | Your API Hash from my.telegram.org |
  | `OWNER_ID` | Your Telegram user ID |
  | `CHANNEL_ID` | Your DB channel ID (e.g. `-100xxxxxxxx`) |
  | `DATABASE_URL` | Your MongoDB connection URL |
  | `DATABASE_NAME` | MongoDB database name |

  ## Optional Variables

  | Variable | Default | Description |
  |----------|---------|-------------|
  | `START_MESSAGE` | Built-in | Bot start message |
  | `PROTECT_CONTENT` | `True` | Prevent files from being forwarded |
  | `CUSTOM_CAPTION` | None | Custom caption for files |
  | `DISABLE_CHANNEL_BUTTON` | `False` | Hide reply markup on DB channel posts |
  | `BAN_SUPPORT` | None | Support link shown to banned users |

  ## Image Variables

  | Variable | Description |
  |----------|-------------|
  | `START_PIC` | Image shown on /start |
  | `FORCE_PIC` | Image shown on force subscribe screen |
  | `PREMIUM_PIC` | Image shown on premium screen |

  ## Flood Protection Variables

  | Variable | Default | Description |
  |----------|---------|-------------|
  | `FLOOD_LIMIT` | `5` | Max messages allowed in the time window |
  | `FLOOD_WINDOW` | `5` | Sliding window duration (seconds) |
  | `FLOOD_BLOCK_DURATION` | `30` | How long user is blocked after flooding (seconds) |

  ## Stats / Analytics Variables

  | Variable | Default | Description |
  |----------|---------|-------------|
  | `STATS_ENABLED` | `True` | Enable activity logging for peak hours tracker |

  </details>

  <img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif">

  ## 𝐶𝑜𝑚𝑚𝑎𝑛𝑑𝑠

  > 💡 The bot ships a button-driven **`/help`** menu that lists every command with description + example. Use it for the most up-to-date inline reference. The list below is the same content for quick GitHub browsing.

  ### 👤 User Commands
  ```
  start      - Start the bot or get files via deep link
  help       - Open the paginated help menu (USER + OWNER + SUPPORT)
  myplan     - Check your premium plan and time remaining
  ```

  ### 🔗 Link Management (Admin)
  ```
  batch         - Generate a range link between two DB-channel messages
  genlink       - Generate a share-link for a single DB-channel message
  custom_batch  - Interactive: send media -> press STOP -> get one batch link
  ```

  ### 📢 Broadcast (Admin)
  ```
  broadcast   - (reply) Send the replied-to message to all users
  pbroadcast  - (reply) Same as /broadcast + pin in every PM
  dbroadcast  - (reply) Auto-deleting broadcast: /dbroadcast <seconds>
  ```

  ### 💎 Premium Management (Admin)
  ```
  addpremium                - /addpremium <user_id> <duration>
                              duration examples: 1h, 1d, 7d, 30d
                              e.g. /addpremium 7137144805 30d
  remove_premium            - /remove_premium <user_id>
  premium_users             - List all active premium users with expiry
  start_premium_monitoring  - (Re)start background expiry monitor
  myplan                    - Check premium status (any user)
  ```

  ### 🧾 Admin Orders (Owner-only — auto-premium flow)
  ```
  id           - /id [today|yesterday|DD-MM-YYYY] — list paid user-ids on a date
  ord          - /ord <user_id> — list every order for a specific user
  amount       - /amount [today|yesterday|DD-MM-YYYY] — total revenue for a date
  stats        - Bot + orders stats (users, paid users, lifetime revenue)
  checkorder   - /checkorder <order_id> — Sellgram + DB lookup (read-only)
  forceverify  - /forceverify <order_id> — re-run verification + recover paid order
  ```

  ### 🛡️ User Management (Admin)
  ```
  ban     - Ban a user from the bot
  unban   - Unban a user
  banlist - List all banned users
  ```

  ### 📡 Force Subscribe (Admin)
  ```
  addchnl   - Add a force subscribe channel
  delchnl   - Remove a force subscribe channel
  listchnl  - View all force subscribe channels
  fsub_mode - Toggle force subscribe mode
  ```

  ### 👮 Admin Management (Admin)
  ```
  add_admin - Add a new admin
  deladmin  - Remove an admin
  admins    - List all admins
  ```

  ### 📊 Analytics (Admin)
  ```
  peakhours    - Today's hourly activity graph (IST)
  weeklyreport - Last 7 days hourly + daily breakdown
  cleanstats   - Remove activity logs older than 30 days
  ```

  ### ⚙️ Settings & Stats (Admin)
  ```
  settings  - Open the inline bot settings panel
  commands  - Legacy short admin-cmds list (kept for backward compat)
  stats     - Check bot uptime + orders stats (see Admin Orders above)
  users     - View total user count
  dlt_time  - Set auto-delete timer for files
  ```

  <img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif">

  ## 🔄 Recent Updates

  Full changelog with code snippets and rationale lives in **[`newadd.md`](./newadd.md)**. Highlights:

  - **v1.8** — Token / Shortner / Anti-Bypass system fully removed — bot is now free-links → premium only
  - **v1.7** — UPI / Sellgram credentials rotated to `paytm.s20gmbu@pty` + new API key
  - **v1.6** — New `/help` command: button-driven, paginated, every command documented with examples
  - **v1.5** — `/custom_batch` double-copy + STOP-junk-link bug fix
  - **v1.4.1** — Channel-post exclusion-list fix kept; auto-delete (DD) reverted on user request
  - **v1.3** — Order-ID prefix changed from `MIKO-` to `ZERO-`
  - **v1.2** — New owner-only Admin Orders panel: `/id`, `/ord`, `/amount`, `/stats`, `/checkorder`, `/forceverify`
  - **v1.0** — Replaced manual gold/platinum tiers with **fully-automatic Sellgram Paytm Status API** verification (UPI deep-link + QR + auto receipt + auto invite)

  <img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif">

  <details>
  <summary><h3>─ <b>ᴅᴇᴩʟᴏʏᴍᴇɴᴛ ᴍᴇᴛʜᴏᴅs</b> ─</h3></summary>

  <h3 align="center">─「 ᴅᴇᴩʟᴏʏ ᴏɴ ʜᴇʀᴏᴋᴜ 」─</h3>
  <p align="center"><a href="https://heroku.com/deploy?template=https://github.com/MikoxYae/Angle-New">
    <img src="https://www.herokucdn.com/deploy/button.svg" alt="Deploy On Heroku">
  </a></p>

  <h3 align="center">─「 ᴅᴇᴩʟᴏʏ ᴏɴ ᴋᴏʏᴇʙ 」─</h3>
  <p align="center"><a href="https://app.koyeb.com/deploy?type=git&repository=github.com/MikoxYae/Angle-New&branch=v2&name=miko-bot">
    <img src="https://www.koyeb.com/static/images/deploy/button.svg" alt="Deploy On Koyeb">
  </a></p>

  <h3 align="center">─「 ᴅᴇᴩʟᴏʏ ᴏɴ ʀᴀɪʟᴡᴀʏ 」─</h3>
  <p align="center"><a href="https://railway.app/deploy?template=https://github.com/MikoxYae/Angle-New">
    <img height="45px" src="https://railway.app/button.svg">
  </a></p>

  <h3 align="center">─「 ᴅᴇᴩʟᴏʏ ᴏɴ ʀᴇɴᴅᴇʀ 」─</h3>
  <p align="center"><a href="https://render.com/deploy?repo=https://github.com/MikoxYae/Angle-New">
    <img src="https://render.com/images/deploy-to-render-button.svg" alt="Deploy to Render">
  </a></p>

  <h3 align="center">─「 ᴅᴇᴩʟᴏʏ ᴏɴ ᴠᴘs 」─</h3>
  <pre>
  git clone -b v2 https://github.com/MikoxYae/Angle-New
  cd Angle-New
  pip3 install -r requirements.txt
  # For 24/7 uptime
  tmux new -s miko
  python3 main.py
  # Detach: Ctrl+B then D
  # Stop: tmux kill-session -t miko
  </pre>

  </details>

  <img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif">

  <h3>「 ᴄʀᴇᴅɪᴛs 」</h3>

  - <b>[ᴅᴇᴠᴇʟᴏᴘᴇʀ](https://t.me/Yae_X_Miko)</b>
  - <b>[ɢɪᴛʜᴜʙ](https://github.com/MikoxYae)</b>
