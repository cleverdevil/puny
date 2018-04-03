from pecan import conf, request

import ZODB, ZODB.FileStorage, BTrees.OOBTree
import persistent
import persistent.list
import transaction
import maya


fs = ZODB.FileStorage.FileStorage(conf.db.path)
db = ZODB.DB(fs)


class Entry(persistent.Persistent):

    def __init__(self, mf2, permalink):
        self.mf2 = mf2
        self.permalink = permalink
        self.deleted = False

    def update(self, mf2):
        self.mf2 = mf2
        self._p_changed = 1

    @property
    def published(self):
        return self.mf2.get('properties', {}).get('published', [None])[0]


class EntryIndex(persistent.Persistent):

    def __init__(self):
        self.all = persistent.list.PersistentList()
        self.by_date = BTrees.OOBTree.OOBTree()
        self.by_permalink = BTrees.OOBTree.OOBTree()
        self.by_category = BTrees.OOBTree.OOBTree()

    def add(self, mf2, permalink):
        # add to "all" list
        entry = Entry(mf2, permalink)
        self.all.append(entry)
        self.all.sort(key=lambda x: x.published)

        # add to permalink index
        self.by_permalink[permalink] = entry

        # add to date index
        published = mf2.get('properties', {}).get('published', [None])[0]
        if published:
            published = maya.parse(published)
            self.by_date.setdefault(published, []).append(entry)

        # add to category index
        categories = mf2.get('properties', {}).get('category', [])
        for category in categories:
            self.by_category.setdefault(category, []).append(entry)

    def delete(self, entry):
        # remove from "all" list
        self.all.remove(entry)

        # remove from permalink index
        del self.by_permalink[entry.permalink]

        # remove from date index
        published = entry.mf2.get('properties', {}).get('published', [None])[0]
        if published:
            published = maya.parse(published)
            self.by_date[published].remove(entry)

        # remove from category index
        categories = mf2.get('properties', {}).get('category', [])
        for category in categories:
            self.by_category[category].remove(entry)

        # tell the object to die in a fire
        del entry


# pecan specific transaction functions


def start():
    request.transaction = transaction.TransactionManager()
    request.dbc = db.open(request.transaction)


def start_read_only():
    start()


def commit():
    request.transaction.commit()


def rollback():
    request.transaction.abort()


def clear():
    request.transaction.abort()
    request.dbc = None
    request.transaction = None


# direct access


def connect():
    if not hasattr(request.dbc.root, 'entries'):
        request.dbc.root.entries = EntryIndex()
    return request.dbc


def store(json):
    conn = connect()
    conn.root.entries.add(json, json['properties']['url'][0])


def get_by_permalink(permalink, hidden=False):
    conn = connect()
    entry = conn.root.entries.by_permalink.get(permalink)
    if entry:
        if entry.deleted:
            if hidden:
                return entry.mf2

        else:
            return entry.mf2


def update(permalink, mf2):
    entry = connect().root.entries.by_permalink.get(permalink)
    if entry:
        entry.update(mf2)


def delete(permalink, soft=False):
    conn = connect()
    entry = conn.root.entries.by_permalink.get(permalink)
    if entry:
        if soft:
            entry.deleted = True
        else:
            conn.root.entries.delete(entry)


def undelete(permalink):
    entry = connect().root.entries.by_permalink.get(permalink)
    if entry:
        entry.deleted = False


def find(limit=20, offset=0):
    conn = connect()

    count = 0
    skipped = 0
    for entry in reversed(conn.root.entries.all):
        if skipped < offset:
            if not entry.deleted:
                skipped += 1
                continue

        if not entry.deleted:
            count += 1
            yield entry.mf2

        if count == limit:
            break
