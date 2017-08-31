from json import loads
import logging

import requests

from . import utils


logger = logging.getLogger('ninegag')


class APIException(Exception):
    pass


class Client(object):
    """
    9GAG API Client.
    """
    class Services:
        """
        Represents sub-API URLs.
        """
        API = 'http://api.9gag.com'
        COMMENT_CDN = 'http://comment-cdn.9gag.com'
        NOTIFY = 'http://notify.9gag.com'
        AD = 'http://ad.9gag.com'
        ADMIN = 'http://admin.9gag.com'

    APP_ID = 'com.ninegag.android.app'

    def __init__(self, app_id=APP_ID, log_level=logging.INFO):
        """
        Create API client instance.

        :param app_id: Application id (defaults to 'com.ninegag.android.app')
        :param log_level: Logging level (defaults to `logging.INFO`)
        """
        logger.level = log_level
        self.app_id = app_id
        self.token = utils.random_sha1()
        self.device_uuid = utils.random_uuid()
        self.userData = None

    def _request(self, method, path, service=Services.API,
                 sign=True, args={}, body={}):
        """
        Perform API request.

        :param method: HTTP method ('GET', 'POST' etc.)
        :param path: URL to retrieve (e.g. '/v2/post-list')
        :param service: :class:`.Client.Services` field, default is `API`
        :param sign: Whether to sign the request or no.
        :param args: URL arguments.
        :param body: Request body ('POST' requests only.)
        :returns: Decoded JSON response.
        :rtype: dict
        """
        url = '/'.join([
            service.strip('/'),
            path.strip('/'),
            '/'.join('{}/{}'.format(k, v) for k, v in args.items()).strip('/')
        ])

        headers = {
            '9GAG-9GAG_TOKEN': self.token,
            '9GAG-TIMESTAMP': str(utils.get_timestamp()),
            '9GAG-APP_ID': self.app_id,
            '9GAG-DEVICE_UUID': self.device_uuid,
            '9GAG-DEVICE_TYPE': 'android',
            '9GAG-BUCKET_NAME': 'MAIN_RELEASE',
            'X-Package-ID': 'com.ninegag.android.app'
        }

        if sign:
            headers['9GAG-REQUEST-SIGNATURE'] = utils.sign_request(
                headers['9GAG-TIMESTAMP'],
                headers['9GAG-APP_ID'],
                headers['9GAG-DEVICE_UUID']
            )

        logging.debug('{} {}: {}\n{}'.format(
            method,
            url,
            body,
            '\n'.join(['{}: {}'.format(k, v) for k, v in headers.items()])
        ))

        if method.upper() in ('GET', 'HEAD', 'OPTIONS'):
            response = requests.get(url, headers=headers)
        else:
            response = requests.post(url, headers=headers, data=body)

        return loads(response.text)

    def _validate_response(self, response):
        """
        Validate the response status.

        :param response: JSON response dictionary.
        :returns: True
        :rtype: bool
        :raises: :class:`.APIException`
        """
        if response['meta']['status'] == 'Success':
            return True
        else:
            raise APIException(response['meta']['errorMessage'])

    def log_in(self, username, password):
        """
        Attempt to log in.

        :param username: User login.
        :param password: User password.
        :returns: True
        :rtype: bool
        :raises: :class:`.APIException`
        """
        response = self._request(
            'GET',
            '/v2/user-token',
            args=dict(
                loginMethod='9gag',
                loginName=username,
                password=utils.md5(password),
                language='en_US',
                pushToken=utils.random_sha1()
            )
        )
        self._validate_response(response)
        self.token = response['data']['userToken']
        self.userData = response['data']
        return True

    def get_posts(self, group=1, type_='hot', count=10,
                  entry_types=['animated', 'photo', 'video', 'album']):
        """
        Fetch posts.

        :param group: Posts category (defaults to 1)
        :param type_: Posts type (defaults to 'hot')
        :param count: Count of posts.
        :param entry_types: list of strings
        :returns: list of :class:`.Post`
        :raises: :class:`.APIException`
        """
        response = self._request(
            'GET',
            '/v2/post-list',
            args=dict(
                group=group,
                type=type_,
                itemCount=count,
                entryTypes=','.join(entry_types)
            )
        )
        self._validate_response(response)
        return list(map(Post, response['data']['posts']))

    @property
    def is_authorized(self):
        """
        Authorization status.
        """
        return self.userData is not None


class Post(object):
    """
    Represents single post.
    """
    def __init__(self, props):
        self.props = props

    @property
    def title(self):
        """
        Post title.
        """
        return self.props['title']

    @property
    def url(self):
        """
        Post url.
        """
        return self.props['url']

    def __str__(self):
        return '<Post title="{}" url={}>'.format(
            self.title.encode('utf-8'),
            self.url.encode('utf-8')
        )

    __repr__ = __str__
