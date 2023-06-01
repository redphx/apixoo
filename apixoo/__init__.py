import hashlib
from typing import Union

import requests

from .const import (
    AlbumInfo,
    ApiEndpoint,
    GalleryCategory,
    GalleryDimension,
    GalleryInfo,
    GallerySorting,
    GalleryType,
    Server,
)
from .pixel_bean import PixelBean
from .pixel_bean_decoder import PixelBeanDecoder


class APIxoo(object):
    HEADERS = {
        'User-Agent': 'Aurabox/3.1.10 (iPad; iOS 14.8; Scale/2.00)',
    }

    def __init__(
        self, email: str, password: str = None, md5_password: str = None, is_secure=True
    ):
        # Make sure at least one password param is passed
        if not any([password, md5_password]):
            raise Exception('Empty password!')

        # Get MD5 hash of password
        if password:
            md5_password = hashlib.md5(password).hexdigest()

        self._email = email
        self._md5_password = md5_password
        self._user = None
        self._request_timeout = 10
        self._is_secure = is_secure

    def _full_url(self, path: str, server: Server = Server.API) -> str:
        """Generate full URL from path"""
        if not path.startswith('/'):
            path = '/' + path

        protocol = 'https://' if self._is_secure else 'http://'
        return '%s%s%s' % (protocol, server.value, path)

    def _send_request(self, endpoint: ApiEndpoint, payload: dict = {}):
        """Send request to API server"""
        if endpoint != ApiEndpoint.USER_LOGIN:
            payload.update(
                {
                    'Token': self._user['token'],
                    'UserId': self._user['user_id'],
                }
            )

        full_url = self._full_url(endpoint.value, Server.API)
        resp = requests.post(
            full_url,
            headers=self.HEADERS,
            json=payload,
            timeout=self._request_timeout,
        )
        return resp.json()

    def set_timeout(self, timeout: int):
        """Set request timeout"""
        self._request_timeout = timeout

    def is_logged_in(self) -> bool:
        """Check if logged in or not"""
        return self._user is not None

    def log_in(self) -> bool:
        """Log in to API server"""
        if self.is_logged_in():
            return True

        payload = {
            'Email': self._email,
            'Password': self._md5_password,
        }

        try:
            resp_json = self._send_request(ApiEndpoint.USER_LOGIN, payload)
            self._user = {
                'user_id': resp_json['UserId'],
                'token': resp_json['Token'],
            }
            return True
        except Exception:
            pass

        return False

    def get_gallery_info(self, gallery_id: int) -> GalleryInfo:
        """Get gallery info by ID"""
        if not self.is_logged_in():
            raise Exception('Not logged in!')

        payload = {
            'GalleryId': gallery_id,
        }

        try:
            resp_json = self._send_request(ApiEndpoint.GET_GALLERY_INFO, payload)
            if resp_json['ReturnCode'] != 0:
                return None

            # Add gallery ID since it isn't included in the response
            resp_json['GalleryId'] = gallery_id
            return GalleryInfo(resp_json)
        except Exception:
            return None

    def get_category_files(
        self,
        category: Union[int, GalleryCategory],
        dimension: GalleryDimension = GalleryDimension.W32H32,
        sort: GallerySorting = GallerySorting.MOST_LIKED,
        file_type: GalleryType = GalleryType.ALL,
        page: int = 1,
        per_page: int = 20,
    ) -> list:
        """Get a list of galleries by Category"""
        if not self.is_logged_in():
            raise Exception('Not logged in!')

        start_num = ((page - 1) * per_page) + 1
        end_num = start_num + per_page - 1

        payload = {
            'StartNum': start_num,
            'EndNum': end_num,
            'Classify': category,
            'FileSize': dimension,
            'FileType': file_type,
            'FileSort': sort,
            'Version': 12,
            'RefreshIndex': 0,
        }

        try:
            resp_json = self._send_request(ApiEndpoint.GET_CATEGORY_FILES, payload)

            lst = []
            for item in resp_json['FileList']:
                lst.append(GalleryInfo(item))

            return lst
        except Exception:
            return None

    def get_album_list(self) -> list:
        """Get Album list in Discover tab"""
        if not self.is_logged_in():
            raise Exception('Not logged in!')

        try:
            resp_json = self._send_request(ApiEndpoint.GET_ALBUM_LIST)
            if resp_json['ReturnCode'] != 0:
                return None

            lst = []
            for item in resp_json['AlbumList']:
                lst.append(AlbumInfo(item))

            return lst
        except Exception:
            return None

    def get_album_files(self, album_id: int, page: int = 1, per_page: int = 20):
        """Get a list of galleries by Album"""
        start_num = ((page - 1) * per_page) + 1
        end_num = start_num + per_page - 1

        payload = {
            'AlbumId': album_id,
            'StartNum': start_num,
            'EndNum': end_num,
        }

        try:
            resp_json = self._send_request(ApiEndpoint.GET_ALBUM_FILES, payload)

            lst = []
            for item in resp_json['FileList']:
                lst.append(GalleryInfo(item))

            return lst
        except Exception:
            return None

    def download(self, gallery_info: GalleryInfo) -> PixelBean:
        """Download and decode animation"""
        url = self._full_url(gallery_info.file_id, server=Server.FILE)
        resp = requests.get(
            url, headers=self.HEADERS, stream=True, timeout=self._request_timeout
        )
        return PixelBeanDecoder.decode_stream(resp.raw)
