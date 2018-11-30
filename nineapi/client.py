from json import loads
import logging

try:
    from urlparse import parse_qsl
except ImportError:
    from urllib.parse import parse_qsl

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
        COMMENT = 'http://comment.9gag.com'
        NOTIFY = 'http://notify.9gag.com'
        AD = 'http://ad.9gag.com'
        ADMIN = 'http://admin.9gag.com'

    class AppIDs:
        COMMENT_CDN = 'a_dd8f2b7d304a10edaf6f29517ea0ca4100a43d1b'

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
        self.generatedAppId = None

    def _request(self, method, path, service=Services.API,
                 sign=True, params={}, args={}, body={}):
        """
        Perform API request.

        :param method: HTTP method ('GET', 'POST' etc.)
        :param path: URL to retrieve (e.g. '/v2/post-list')
        :param service: :class:`.Client.Services` field, default is `API`
        :param sign: Whether to sign the request or no.
        :param args: URL arguments (converted to weird form like `/count/10/type/hot/...`)
        :param query: Query args (converted to `?foo=bar&...`)
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
            'X-Package-ID': self.app_id,
            '9GAG-DEVICE_UUID': self.device_uuid,
            'X-Device-UUID': self.device_uuid,
            '9GAG-DEVICE_TYPE': 'android',
            '9GAG-BUCKET_NAME': 'MAIN_RELEASE',
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

        if method.upper() == 'GET':
            response = requests.get(url, headers=headers, params=params)
        elif method.upper() == 'POST':
            response = requests.post(url, headers=headers, data=body, params=params)
        else:
            raise NotImplementedError('Only GET and POST methods are currently implemented.')

        data = loads(response.text)

        self._validate_response(data)

        return data

    def _validate_response(self, response):
        """
        Validate the response status.

        :param response: JSON response dictionary.
        :returns: True
        :rtype: bool
        :raises: :class:`.APIException`
        """
        if 'meta' in response:
            if response['meta']['status'] == 'Success':
                return True
            else:
                raise APIException(response['meta']['errorMessage'])
        elif 'status' in response:
            if response['status'] == 'ERROR':
                raise APIException(response['error'])
            return True

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
        self.token = response['data']['userToken']
        self.userData = response['data']
        self.generatedAppId = dict(parse_qsl(self.userData['noti']['readStateParams']))['appId']
        # self.generatedAppId = dict(parse_qsl(self.userData['noti']['chatBadgeReadStateParams']))['appId']
        return True

    def get_posts(self, group=1, type_='hot', count=10,
                  entry_types=['animated', 'photo', 'video', 'album'],
                  olderThan=None, **kwargs):
        """
        Fetch posts.

        :param group: Posts category (defaults to 1)
        :param type_: Posts type (defaults to 'hot')
        :param count: Count of posts.
        :param entry_types: list of strings
        :param olderThan: Last seen post (for pagination) - `str`,
                          :class:`Post` or `None`
        :returns: list of :class:`.Post`
        :raises: :class:`.APIException`
        """
        args = dict(
            group=group,
            type=type_,
            itemCount=count,
            entryTypes=','.join(entry_types),
            offset=10,
            **kwargs
        )
        if olderThan is not None:
            if isinstance(olderThan, Post):
                olderThan = olderThan.id
            args['olderThan'] = olderThan
        response = self._request(
            'GET',
            '/v2/post-list',
            args=args
        )
        return list([Post(self, post) for post in response['data']['posts']])

    def search_posts_by_tag(self, query, offset=0, count=10,
                            entry_types=['animated', 'photo', 'video', 'album'],
                            sort='asc', **kwargs):
        """
        Fetch posts that match specific tag.

        :param query: Posts tag
        :param offset: Offset to start from.
        :param count: Count of posts.
        :param entry_types: list of strings
        :param sort: sorting order ("asc" or "desc") - does not seem to work
        :returns: list of :class:`.Post`
        :raises: :class:`.APIException`
        """
        args = dict(
            query=query,
            fromIndex=offset,
            itemCount=count,
            entryTypes=','.join(entry_types),
            offset=10,
            sort=sort,
            **kwargs
        )
        response = self._request(
            'GET',
            '/v2/tag-search',
            args=args
        )
        return list([Post(self, post) for post in response['data']['posts']])

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

    class Types(object):
        """
        Enum for possible post type values.
        """

        Photo = 'Photo'
        Animated = 'Animated'

    def __init__(self, client, props):
        self._client = client
        self._props = props

    @property
    def id(self):
        """
        Post ID.
        """
        return self._props['id']

    @property
    def title(self):
        """
        Post title.
        """
        return self._props['title']

    @property
    def url(self):
        """
        Post url.
        """
        return self._props['url']

    @property
    def type(self):
        """
        Post type.
        """
        return self._props['type']

    @property
    def props(self):
        """
        Dictionary with post data.
        """
        return self._props

    def get_media_url(self):
        """
        Returns image URL for Photo posts and .WEBM URL for Animated posts.
        """
        if self.type == Post.Types.Photo:
            return self.props['images']['image700']['url']
        elif self.type == Post.Types.Animated:
            return self.props['images']['image460sv']['url']
        raise NotImplementedError(
            'Post type not implemented: {}, '
            'you can report it here: '
            'https://github.com/and3rson/nineapi/issues'.format(
                self.type
            )
        )

    def get_top_comments(self):
        """
        Retrieves top comments for this post.
        """

        response = self._client._request(
            'GET',
            '/v1/topComments.json',
            service=Client.Services.COMMENT_CDN,
            params=dict(
                appId=Client.AppIDs.COMMENT_CDN,
                urls=self.url,
                commentL1=5,
                commentL2=5,
                pretty=0
            )
        )

        """
        response = self._client._request(
            'GET',
            '/v1/comment.json',
            service=Client.Services.COMMENT,
            params=dict(
                appId=Client.AppIDs.COMMENT_CDN,
                urls=self.url,
                order='score',
                direction='desc',
                count=10,
                level=2,
                ref='score_00000000_00000000',
                auth=self._client.userData['commentAuth']['authHash']
            )
        )
        """

        return list([Comment(self._client, self, comment) for comment in response['payload']['data'][0]['comments']])

    def __str__(self):
        return '<Post id="{}" title="{}" url={}>'.format(
            self.id,
            self.title.encode('utf-8'),
            self.url
        )

    __repr__ = __str__


class Comment(object):
    def __init__(self, client, post, props):
        self._client = client
        self._post = post
        self._props = props

    @property
    def id(self):
        """
        Comment ID.
        """
        return self._props['commentId']

    @property
    def text(self):
        """
        Comment text. Contains GIF url for GIT comments.
        """
        return self._props['text']

    @property
    def url(self):
        """
        Comment url.
        """
        return self._props['url']

    @property
    def post(self):
        """
        Returns the associated :class:`Post`.
        """
        return self._post

    @property
    def children(self):
        """
        Returns comments that are children for this one.
        """
        return [Comment(self._client, self._post, comment) for comment in self._props['children']]

    @property
    def props(self):
        """
        Dictionary with comment data.
        """
        return self._props

    def get_media_url(self):
        """
        Returns media URL associated with this comment.
        """
        if 'media' in self._props:
            medias = self._props['media'][0]['imageMetaByType']
            if medias['type'] == 'ANIMATED':
                return medias['video']['url']
            else:
                return medias['image']['url']

    def __str__(self):
        return '<Comment id="{}" post="{}" text="{}">'.format(
            self.id,
            self._post.id,
            self.text.encode('utf-8')
        )

    __repr__ = __str__

