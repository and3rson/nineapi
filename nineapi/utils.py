import uuid
import hashlib
from time import time


def random_uuid():
    """
    Generate random UUID string.
    """
    return uuid.uuid4().hex


def random_sha1():
    """
    Generate random SHA1 string.
    """
    sha = hashlib.sha1()
    sha.update(str(get_timestamp()).encode('latin'))
    return sha.hexdigest()


def get_timestamp():
    """
    Generate timestamp in milliseconds.
    """
    return int(time() * 1000)


def sign_request(timestamp, app_id, device_uuid):
    """
    Generate signature for HTTP request.
    """
    sha = hashlib.sha1()
    sha.update('*{}_._{}._.{}9GAG'.format(
        timestamp, app_id, device_uuid
    ).encode('latin'))
    return sha.hexdigest()


def md5(string):
    """
    Hash string with MD5.
    """
    digest = hashlib.md5()
    digest.update(string.encode('latin'))
    return digest.hexdigest()
