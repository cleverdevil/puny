from pecan import conf
from slugify import UniqueSlugify
from . import storage

import uuid


def unique_check(text, uids):
    permalink = conf.app.public_url + '/view/entry/' + text
    return storage.get_by_permalink(permalink, hidden=True) is None


slugify_unique = UniqueSlugify(unique_check=unique_check)


def generate_slug(mf2):
    seed = None

    props = mf2.get('properties', {})
    if 'name' in props:
        seed = props['name'][0]
    elif 'content' in props:
        if len(props['content']):
            for content in props['content']:
                if isinstance(content, dict):
                    if 'value' in content:
                        seed = content['value']
                    elif 'html' in content:
                        seed = content['html']
                elif isinstance(content, str):
                    seed = content

    if len(seed) == 0:
        if 'like-of' in props:
            seed = 'like of ' + props['like-of'][0]
        elif 'bookmark-of' in props:
            seed = 'bookmark of ' + props['bookmark-of'][0]
        elif 'repost-of' in props:
            seed = 'repost-of ' + props['repost-of'][0]
        else:
            seed = str(uuid.uuid4())

    return slugify_unique(seed, to_lower=True, max_length=20)
