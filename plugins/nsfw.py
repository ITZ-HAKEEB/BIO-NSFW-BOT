"""NSFW filter - runs fully offline: NudeNet ONNX model (bundled in the pip package).
No API key, no internet needed at runtime.

Scans photos, stickers, GIFs/videos (thumbnail + a few frames), image files and the
sender's PROFILE PHOTO. Bad -> message deleted + short warning.
Scanning runs in a background task, so the bot never freezes while a photo is checked.
"""
import asyncio
import logging
import os
import tempfile
import threading
import time
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor

from telegram.ext import MessageHandler, filters

import config
from database import db
from helpers import _send_notice, is_admin, warn

NAME = "nsfw"
HELP = \
"""<u>⊙ NSFW FILTER :</u>

<blockquote>🔞 Scans photos, stickers, GIFs, videos and image files with an offline AI model (no API) and deletes adult content.</blockquote>

<blockquote>↣ /nsfw on : Enable NSFW filter...!
↣ /nsfw off : Disable NSFW filter..!</blockquote>

<blockquote>⚠️ <b>Action :</b>
— NSFW media is deleted and a warning is sent.
— If a user's profile photo is NSFW, all their messages are deleted until they change it.</blockquote>

<blockquote>⚠️ <b>Note :</b>
— Group admins and approved users are always exempt.
— 👮 Only group admins can configure this setting.</blockquote>"""
REASON = "NSFW content"
PROFILE_REASON = "NSFW profile photo"

log = logging.getLogger("meowguard.nsfw")
MB = 1024 * 1024

_pool = ThreadPoolExecutor(max_workers=2)       # CPU work happens here, not in the event loop
_det = None
_det_failed = False
_det_lock = threading.Lock()
_results = OrderedDict()                        # file_unique_id -> bool (same image again = instant)
_profiles = {}                                  # user_id -> (checked_at, bad, photo_unique_id)
_notice_at = {}                                 # user_id -> last profile warning time


# ---------------------------------------------------------------- model
def load_model():
    """Load the model once (called at startup and lazily). Returns detector or None."""
    global _det, _det_failed
    if _det is not None or _det_failed:
        return _det
    with _det_lock:
        if _det is None and not _det_failed:
            try:
                from nudenet import NudeDetector
                _det = NudeDetector()
                log.info("NSFW model loaded (threshold %.2f)", config.NSFW_THRESHOLD)
            except Exception as e:
                _det_failed = True
                log.error("NSFW filter OFF - nudenet could not be loaded: %s", e)
    return _det


def _flagged(dets):
    return any(d.get("class") in config.NSFW_LABELS and d.get("score", 0) >= config.NSFW_THRESHOLD
               for d in dets or [])


def _detect_path(path):
    det = load_model()
    if det is None:
        return False
    try:
        return _flagged(det.detect(path))
    except Exception as e:
        log.warning("detect failed: %s", e)
        return False


def _detect_bytes(data):
    fd, path = tempfile.mkstemp(suffix=".jpg")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        return _detect_path(path)
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


def _detect_video(data):
    """Check 3 frames (20% / 50% / 80%) of a video / GIF."""
    import cv2
    fd, path = tempfile.mkstemp(suffix=".mp4")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        cap = cv2.VideoCapture(path)
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        points = (0.2, 0.5, 0.8) if total >= 3 else (0,)
        for i, p in enumerate(points):
            if total:
                cap.set(cv2.CAP_PROP_POS_FRAMES, int(total * p))
            ok, frame = cap.read()
            if not ok:
                continue
            fpath = f"{path}.{i}.jpg"
            try:
                cv2.imwrite(fpath, frame)
                if _detect_path(fpath):
                    return True
            finally:
                try:
                    os.remove(fpath)
                except OSError:
                    pass
        cap.release()
        return False
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


# ---------------------------------------------------------------- scanning
def _remember(key, bad):
    _results[key] = bad
    while len(_results) > 3000:
        _results.popitem(last=False)


async def _download(context, file_id):
    f = await context.bot.get_file(file_id)
    return bytes(await f.download_as_bytearray())


async def _scan(context, f, video=False):
    key = f.file_unique_id
    if key in _results:
        return _results[key]
    try:
        data = await _download(context, f.file_id)
        fn = _detect_video if video else _detect_bytes
        bad = await asyncio.get_running_loop().run_in_executor(_pool, fn, data)
    except Exception as e:                      # fail open: never delete because of an error
        log.warning("scan failed: %s", e)
        return False
    _remember(key, bad)
    return bad


def _pick(sizes):
    """Telegram sends several sizes; ~800px is plenty for the model and fast to download."""
    for p in sizes:
        if max(p.width, p.height) >= 640:
            return p
    return sizes[-1]


def _video_ok(v):
    return config.NSFW_SCAN_VIDEO and (v.file_size or 0) <= config.NSFW_VIDEO_MAX_MB * MB


def _sources(msg):
    """[(file, is_video)] to scan for this message."""
    out, seen = [], set()

    def add(f, video=False):
        if f is not None and f.file_unique_id not in seen:
            seen.add(f.file_unique_id)
            out.append((f, video))

    if msg.photo:
        add(_pick(msg.photo))
    st = msg.sticker
    if st:
        if st.is_animated or st.is_video:
            add(st.thumbnail)                   # .tgs / .webm: first frame preview only
        else:
            add(st)
    for v in (msg.video, msg.animation, msg.video_note):
        if v:
            add(v.thumbnail)
            if _video_ok(v):
                add(v, True)
    d = msg.document
    if d:
        mime = d.mime_type or ""
        if mime.startswith("image/") and (d.file_size or 0) <= config.NSFW_MAX_IMAGE_MB * MB:
            add(d)
        else:
            add(d.thumbnail)
            if mime.startswith("video/") and _video_ok(d):
                add(d, True)
    return out


async def _profile_bad(context, user):
    now = time.time()
    hit = _profiles.get(user.id)
    if hit and now - hit[0] < config.NSFW_PROFILE_CACHE_TTL:
        return hit[1]
    bad, uid = False, None
    try:
        res = await context.bot.get_user_profile_photos(user.id, limit=1)
        if res.total_count and res.photos:
            sizes = res.photos[0]
            uid = sizes[-1].file_unique_id
            bad = hit[1] if (hit and hit[2] == uid) else await _scan(context, _pick(sizes))
    except Exception as e:                      # hidden by privacy settings etc. -> treat as clean
        log.debug("profile photo check failed: %s", e)
    _profiles[user.id] = (now, bad, uid)
    return bad


async def _process(context, msg, user):
    for f, video in _sources(msg):
        if await _scan(context, f, video):
            return await warn(context, msg, user, REASON)
    if await _profile_bad(context, user):
        try:
            await msg.delete()
        except Exception as e:
            log.warning("cannot delete (need 'Delete messages' right): %s", e)
            return
        if time.time() - _notice_at.get(user.id, 0) > 30:     # don't spam warnings
            _notice_at[user.id] = time.time()
            await _send_notice(context, msg, user,
                               f"{PROFILE_REASON} is not allowed here. Change your profile photo to chat.")


async def watch(update, context):
    msg, chat, user = update.effective_message, update.effective_chat, update.effective_user
    if not msg or not user or chat.type not in ("group", "supergroup"):
        return
    if msg.sender_chat or msg.is_automatic_forward or user.is_bot:
        return
    if msg.new_chat_members or msg.left_chat_member:
        return
    s = db.get(chat.id)
    if not s["mods"].get(NAME) or user.id in s["approved"]:
        return
    if await is_admin(chat.id, user.id, context):
        return
    # background task: a slow scan must not block the other updates
    context.application.create_task(_process(context, msg, user), update=update)


def register(app):
    # group=1 -> runs in addition to the normal guard (group 0)
    app.add_handler(MessageHandler(filters.ChatType.GROUPS & ~filters.COMMAND, watch), group=1)
