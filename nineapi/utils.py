import uuid
import hashlib
from time import time


def random_uuid():
    return uuid.uuid4().hex


def random_sha1():
    sha = hashlib.sha1()
    sha.update(str(get_timestamp()).encode('latin'))
    return sha.hexdigest()


def get_timestamp():
    return int(time() * 1000)


def sign_request(timestamp, app_id, device_uuid):
    sha = hashlib.sha1()
    sha.update('*{}_._{}._.{}9GAG'.format(
        timestamp, app_id, device_uuid
    ).encode('latin'))
    return sha.hexdigest()


def md5(string):
    digest = hashlib.md5()
    digest.update(string.encode('latin'))
    return digest.hexdigest()
