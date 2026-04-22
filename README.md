<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif">

  <h2 align="center">
      ──「ᴍɪᴋᴏ ᴀᴅᴠᴀɴᴄᴇ ᴛᴏᴋᴇɴ ғɪʟᴇ sʜᴀʀɪɴɢ ʙᴏᴛ」──
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
  • <b>Token Verification:</b> Secure access via shortlink token with anti-bypass protection

  <b>🆓 Free Link System (with ON/OFF toggle):</b>

  • <b>Daily Free Links:</b> Every user gets N free file links per day (default 5, configurable from Settings)
  • <b>Free Link ON/OFF toggle:</b> Disable the free quota entirely from <b>Settings → Free Link</b>
  • <b>Bypass:</b> Admins, Owner, and Premium users skip the daily limit entirely
  • <b>Auto Reset:</b> Daily count resets automatically — no cron job needed
  • <b>Presets:</b> 5 / 10 / 15 / 20 / Custom — configurable from Settings panel

  <b>🔗 Free Link × Shortner — 4 Access Modes:</b>

  | Free Link | Shortner | Behavior |
  |-----------|----------|----------|
  | 🟢 ON  | 🟢 ON  | N free links/day → then token required |
  | 🟢 ON  | 🔴 OFF | N free links/day → then premium required |
  | 🔴 OFF | 🟢 ON  | <b>Direct token flow</b> — verify once, valid for `VERIFY_EXPIRE` time |
  | 🔴 OFF | 🔴 OFF | <b>Unlimited free access</b> — no limits, no token, no premium prompt |

  • Toggle Shortner ON/OFF from <b>Settings → Shortner</b>
  • Toggle Free Link ON/OFF from <b>Settings → Free Link</b>
  • Mix and match — bot adapts the access flow automatically

  <b>💎 Premium Tier System:</b>

  | Tier | Token Bypass | Free Link Bypass | Protect Content Bypass | Force Sub Bypass |
  |------|:---:|:---:|:---:|:---:|
  | 🥇 Gold | ✅ | ✅ | ✅ | ❌ |
  | 💎 Platinum | ✅ | ✅ | ✅ | ✅ |

  • Auto expiry notification — 24h reminder + 1h final reminder
  • Auto removal when premium expires — no manual cleanup needed
  • `/myplan` — users can check their tier and time remaining

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
  • Toggle protect content, anti-bypass, shortner settings from `/settings`
  • Shortner URL/API/expire time configurable from panel
  • <b>Free Link panel</b> — toggle Free Link ON/OFF and set daily limit (5/10/15/20/Custom)
  • <b>Shortner toggle</b> — switch between token mode and premium-only mode
  • <b>Combine both toggles</b> for 4 different access modes (see Free Link × Shortner table above)

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
  | `PREMIUM_PIC` | Image shown on token/premium screen |

  ## Token / Shortner Variables

  | Variable | Default | Description |
  |----------|---------|-------------|
  | `SHORTLINK_URL` | — | Shortner domain (e.g. `linkshortify.com`) |
  | `SHORTLINK_API` | — | Shortner API key |
  | `VERIFY_EXPIRE` | `60` | Token validity in seconds |
  | `TUT_VID` | — | Tutorial video link shown on token screen |
  | `ANTI_BYPASS_ENABLED` | `True` | Enable anti-bypass protection |
  | `ANTI_BYPASS_MIN_WAIT` | `8` | Minimum wait time for verification (seconds) |
  | `ANTI_BYPASS_BLOCK_SCORE` | `70` | Risk score threshold for blocking |
  | `WEB_VERIFY_BASE_URL` | — | Public URL for web verification page |

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

  ### 👤 User Commands
  ```
  start      - Start the bot or get files
  myplan     - Check your premium tier and time remaining
  ```

  ### 🔗 Link Management (Admin)
  ```
  batch         - Create link for multiple posts
  genlink       - Create link for a single post
  custom_batch  - Create custom batch from channel/group
  ```

  ### 📢 Broadcast (Admin)
  ```
  broadcast   - Broadcast text message to all users
  dbroadcast  - Broadcast document/video to all users
  pbroadcast  - Broadcast photo to all users
  ```

  ### 👑 Premium Management (Admin)
  ```
  addpremium     - Add premium user: /addpremium user_id time unit tier
                   Tiers: gold | platinum
                   Example: /addpremium 123456 1 d gold
  remove_premium - Remove premium from a user
  premium_users  - List all active premium users with tier info
  myplan         - Check premium status (any user)
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
  settings  - Open bot settings panel
  stats     - Check bot uptime
  users     - View total user count
  count     - Count shortner clicks
  dlt_time  - Set auto-delete timer for files
  ```

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
