from pecan import conf
from hashfs import HashFS


fs = HashFS(conf.media.upload_root, depth=4, width=1, algorithm='sha256')


def upload_file(upload, filename):
    ext = ''
    if '.' in filename:
        ext = '.' + filename.rsplit('.', 1)[1]

    addr = fs.put(upload, extension=ext)
    return conf.app.public_url + '/u/' + addr.relpath
