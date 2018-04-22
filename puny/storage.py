from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, DateTime, JSON, Boolean, create_engine
from sqlalchemy.orm import sessionmaker
from pecan import conf, request

import urllib.parse
import json
import boto3
import maya


# define model objects
Base = declarative_base()

class Post(Base):
    __tablename__ = 'posts'

    permalink = Column(String(256), primary_key=True)
    published = Column(DateTime)
    deleted = Column(Boolean, default=False)
    mf2 = Column(JSON)


# pecan specific transaction functions
engine = None
Session = None
def init():
    global engine
    global Session

    engine = create_engine(conf.db.url)
    Session = sessionmaker(bind=engine)
    Base.metadata.bind = engine
    Base.metadata.create_all()


def start():
    request.session = Session()


def start_read_only():
    request.session = Session()


def commit():
    request.session.commit()


def rollback():
    request.session.rollback()


def clear():
    request.session.close()


# direct access

def _slug(permalink):
    return urllib.parse.urlparse(permalink).path


def store(mf2):
    if not mf2['properties'].get('published'):
        mf2['properties']['published'] = maya.now().datetime().isoformat()

    permalink = mf2['properties']['url'][0]
    published = maya.parse(mf2['properties']['published'][0]).datetime()

    post = Post(
        permalink=_slug(permalink),
        published=published,
        mf2=mf2,
        deleted=False
    )
    request.session.add(post)


def get_by_permalink(permalink, hidden=False, return_object=False):
    post = request.session.query(Post).get(_slug(permalink))

    if post:
        if post.deleted:
            if hidden:
                return post if return_object else post.mf2
        else:
            return post if return_object else post.mf2


def update(permalink, mf2):
    post = get_by_permalink(permalink, return_object=True, hidden=True)
    if not post:
        return

    post.mf2 = mf2
    post.published = maya.parse(mf2['properties']['published'][0]).datetime()
    request.session.add(post)


def delete(permalink, soft=False):
    post = get_by_permalink(permalink, return_object=True, hidden=True)
    if post:
        if soft:
            post.deleted = True
            request.session.add(post)
        else:
            request.session.delete(post)


def undelete(permalink):
    post = get_by_permalink(permalink, return_object=True, hidden=True)
    if post:
        post.deleted = False
        request.session.add(post)


def find(limit=20, offset=0, category=None):
    posts = request.session.query(Post).filter(
        Post.deleted == False
    )

    if category:
        print(category)
        posts = posts.filter(
            Post.mf2['properties']['category'].comparator.contains(category)
        )

    posts = posts.order_by(-Post.published).limit(limit).offset(offset)

    for post in posts:
        yield post.mf2
