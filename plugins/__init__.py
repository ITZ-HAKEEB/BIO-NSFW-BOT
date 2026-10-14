from telegram.ext import CommandHandler, filters

from helpers import make_toggle
from plugins import (abuse, approve as _approve, biomode, fsub as _fsub, edit, echo as _echo, linkfilter, mediadelete, msgdelete,
                     nohashtags, nophone, nopromo, noforward, nostylish, nsfw, purge as _purge)

# order = order in which filters run
FILTERS = [noforward, nohashtags, nophone, linkfilter, nopromo, nostylish, abuse, biomode]
TOGGLE_MODULES = FILTERS + [edit, nsfw]   # nsfw has its own background handler (see plugins/nsfw.py)
ALL = {m.NAME: m for m in TOGGLE_MODULES + [mediadelete, msgdelete, _echo, _purge, _approve, _fsub]}


def register_all(app):
    from plugins import start, settings, guard, image, broadcast, logs
    start.register(app)
    for m in TOGGLE_MODULES:
        app.add_handler(CommandHandler(m.NAME, make_toggle(m.NAME), filters=filters.ChatType.GROUPS))
    for m in (abuse, nsfw, mediadelete, msgdelete, _echo, _purge, _approve, _fsub, settings, image, broadcast, logs):
        m.register(app)
    guard.register(app)  # last, catch-all message guard
