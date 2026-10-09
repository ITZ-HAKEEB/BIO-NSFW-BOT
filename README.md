# Meow Guard Bot

Telegram group security bot, one file per module.

```
bot.py            entry point
config.py         ALL settings (env vars, texts, tuning)
database.py       MongoDB / local JSON storage
helpers.py        admin check, warn, delete-later, toggle helpers
plugins/
  approve.py     fsub.py                                    (approve users / force subscribe)
  nohashtags.py  nopromo.py  nophone.py  noforward.py  nostylish.py
  biomode.py     linkfilter.py  abuse.py  edit.py          (filters)
  mediadelete.py msgdelete.py                               (timers)
  echo.py  purge.py  settings.py  start.py                  (commands/UI)
  broadcast.py     owner-only /broadcast and /stats
  guard.py         runs every enabled filter on each message
  __init__.py      plugin registry
```

## Add a new filter
Create `plugins/myfilter.py` with `NAME`, `HELP` and `async def check(context, msg, user, text, etypes)`
(return a reason string to delete, else None), then add it to `FILTERS` in `plugins/__init__.py`.

## Config (Heroku Config Vars)
`BOT_TOKEN` (required), `MONGO_URI` (recommended), `BOT_NAME`, `OWNER_URL`, `UPDATE_CHANNEL_URL`, `SUPPORT_URL`, `SOURCE_URL`, `FSUB_CACHE_TTL`,
`WARN_DELETE_AFTER`, `ADMIN_CACHE_TTL`, `BIO_CACHE_TTL`, `STYLISH_MIN_CHARS`, `DEFAULT_BAD_WORDS`.

## Deploy on Heroku
1. Push repo to GitHub -> Heroku New App -> Deploy -> connect repo.
2. Settings -> Config Vars -> add `BOT_TOKEN` and `MONGO_URI`.
3. Deploy Branch, then Resources -> turn ON `worker` (turn `web` off).
CLI: `heroku config:set BOT_TOKEN=xxx MONGO_URI=xxx && git push heroku main && heroku ps:scale worker=1`

## Use
Add bot to group as admin (Delete messages). Admin commands: `/linkfilter on`, `/nopromo on`, `/abuse on`,
`/addabuse word`, `/mediadelete 30`, `/msgdelete 60`, `/approve` (reply), `/unapprove`, `/approved`, `/fsub @channel`, `/echo text`, `/purge` (reply), `/settings`.
Admins are never filtered.

## Font & photo
- Every bot text uses the small-caps font (`fonts.py`). Set `FONT_STYLE=off` to disable.
- Photo on /start and help: set `OWNER_ID` (your Telegram id), then in the bot's PM send a photo with caption
  `/setimage` (or reply to a photo with `/setimage`). `/delimage` removes it. Or set `START_IMAGE` (URL/file_id).

## MongoDB (so users, groups & settings survive Heroku restarts)
1. mongodb.com/atlas -> free M0 cluster -> Database Access: create a user + password.
2. Network Access -> Add IP `0.0.0.0/0` (Heroku IPs change).
3. Connect -> Drivers -> copy the `mongodb+srv://...` string, put your password in it
   (special characters must be URL-encoded) and set it as `MONGO_URI` in Heroku Config Vars.
Collections created automatically in DB `meowguard`: `chats` (settings), `users`, `groups`.
If `MONGO_URI` is wrong the bot stops at startup with a clear error. Without it, data.json is used (lost on Heroku restart).

## Broadcast (owner only, in the bot's PM; needs `OWNER_ID`)
- Reply to any message with `/broadcast` -> copied to everyone (photos/buttons/format kept, no forward tag).
- `/broadcast your text` -> plain text.
- Flags: `-users`, `-groups`, `-pin` (pin in groups). Default = users + groups.
- `/stats` shows how many users and groups are saved.
Users are saved when they `/start` the bot, groups when the bot is added or sees a message.
Blocked users / groups that removed the bot are cleaned from the list automatically.
