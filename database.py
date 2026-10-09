import json, os, time

import config

DEFAULT = {"mods": {}, "words": [], "msgdelete": None, "mediadelete": None, "approved": [], "fsub": None}


class Database:
    """MongoDB if MONGO_URI is set, otherwise a local JSON file (data.json).

    Mongo collections: `chats` (settings per chat), `users` (bot PM users), `groups` (groups bot is in).
    """

    def __init__(self):
        self.cache = {}
        self.col = self.ucol = self.gcol = None
        self._seen = {"users": set(), "groups": set()}   # skip repeat writes within one run
        if config.MONGO_URI:
            from pymongo import MongoClient
            client = MongoClient(config.MONGO_URI, serverSelectionTimeoutMS=8000)
            try:
                client.admin.command("ping")
            except Exception as e:
                raise SystemExit(f"MongoDB connection failed: {e}\n"
                                 "Check MONGO_URI, the password (URL-encode special chars) and Atlas "
                                 "Network Access (allow 0.0.0.0/0 for Heroku).")
            d = client[config.DB_NAME]
            self.col, self.ucol, self.gcol = d["chats"], d["users"], d["groups"]
        else:
            self.path = "data.json"
            if os.path.exists(self.path):
                with open(self.path) as f:
                    self.cache = {int(k): v for k, v in json.load(f).items()}

    # ---------- per-chat settings ----------
    def get(self, chat_id):
        if chat_id not in self.cache:
            doc = self.col.find_one({"_id": chat_id}) if self.col is not None else None
            base = json.loads(json.dumps(DEFAULT))
            if doc:
                base.update({k: v for k, v in doc.items() if k != "_id"})
            self.cache[chat_id] = base
        for k, v in DEFAULT.items():          # old chats / data.json may miss new keys
            self.cache[chat_id].setdefault(k, json.loads(json.dumps(v)))
        return self.cache[chat_id]

    def save(self, chat_id):
        doc = self.cache[chat_id]
        if self.col is not None:
            self.col.replace_one({"_id": chat_id}, {"_id": chat_id, **doc}, upsert=True)
        else:
            with open(self.path, "w") as f:
                json.dump({str(k): v for k, v in self.cache.items()}, f)

    # ---------- broadcast targets: kind = "users" | "groups" ----------
    def _col(self, kind):
        return self.ucol if kind == "users" else self.gcol

    def add(self, kind, _id):
        if _id in self._seen[kind]:
            return
        self._seen[kind].add(_id)
        if self.col is not None:
            self._col(kind).update_one({"_id": _id}, {"$setOnInsert": {"added": int(time.time())}}, upsert=True)
        else:
            lst = self.get(0).setdefault(kind, [])
            if _id not in lst:
                lst.append(_id)
                self.save(0)

    def remove(self, kind, _id):
        self._seen[kind].discard(_id)
        if self.col is not None:
            self._col(kind).delete_one({"_id": _id})
        else:
            lst = self.get(0).setdefault(kind, [])
            if _id in lst:
                lst.remove(_id)
                self.save(0)

    def ids(self, kind):
        if self.col is not None:
            return [d["_id"] for d in self._col(kind).find({}, {"_id": 1})]
        return list(self.get(0).setdefault(kind, []))

    def count(self, kind):
        if self.col is not None:
            return self._col(kind).count_documents({})
        return len(self.get(0).setdefault(kind, []))

    def add_user(self, uid):
        self.add("users", uid)

    def add_group(self, cid):
        self.add("groups", cid)


db = Database()
