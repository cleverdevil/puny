from pecan import conf
from datetime import datetime

import boto3
import uuid


s3 = boto3.client('s3')


def upload_file(upload, filename):
    ext = ''
    if '.' in filename:
        ext = '.' + filename.rsplit('.', 1)[1]

    now = datetime.utcnow()
    u = str(uuid.uuid4())[:8]

    key = '%s/%s/%s/%s%s' % (
        now.year,
        now.month,
        now.day,
        u,
        ext
    )

    s3.put_object(Bucket=conf.s3.bucket_name, Key=key, Body=upload)

    return '/media/view/' + key


def get_file(key):
    try:
        response = s3.get_object(Bucket=conf.s3.bucket_name, Key=key)
    except:
        return None
    else:
        return response['Body']
