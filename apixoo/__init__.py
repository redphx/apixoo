import hashlib

import requests

from .const import (
    REQUESTS_TIMEOUT,
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

    def __init__(self, email: str, password: str = None, md5_password: str = None):
        # Make sure at least one password param is passed
        if not any([password, md5_password]):
            raise Exception('Empty password!')

        # Get MD5 hash of password
        if password:
            md5_password = hashlib.md5(password).hexdigest()

        self._email = email
        self._md5_password = md5_password
        self._user = None

    def _full_url(self, path: str, server: Server = Server.API) -> str:
        if not path.startswith('/'):
            path = '/' + path

        return server + path

    def is_logged_in(self) -> bool:
        return self._user is not None

    def log_in(self) -> bool:
        if self.is_logged_in():
            return True

        payload = {
            'Email': self._email,
            'Password': self._md5_password,
        }

        try:
            resp = requests.post(
                self._full_url('/UserLogin'),
                headers=self.HEADERS,
                json=payload,
                timeout=REQUESTS_TIMEOUT,
            )
            resp_json = resp.json()
            return_code = resp_json.get('ReturnCode')
            if return_code == 0:
                self._user = {
                    'user_id': resp_json['UserId'],
                    'token': resp_json['Token'],
                }
                return True
        except Exception:
            pass

        return False

    def get_gallery_info(self, gallery_id: int) -> GalleryInfo:
        if not self.is_logged_in():
            raise Exception('Not logged in!')

        payload = {
            'Token': self._user['token'],
            'UserId': self._user['user_id'],
            'GalleryId': gallery_id,
        }

        resp = requests.post(
            self._full_url('/Cloud/GalleryInfo'),
            headers=self.HEADERS,
            json=payload,
            timeout=REQUESTS_TIMEOUT,
        )
        resp_json = resp.json()
        if resp_json['ReturnCode'] != 0:
            return None

        # Add gallery ID since it isn't included in the response
        resp_json['GalleryId'] = gallery_id
        return GalleryInfo(resp_json)

    def get_category_files(
        self,
        category: int | GalleryCategory,
        dimension: GalleryDimension = GalleryDimension.W32H32,
        sort: GallerySorting = GallerySorting.MOST_LIKED,
        file_type: GalleryType = GalleryType.ALL,
        page: int = 1,
        per_page: int = 20,
    ) -> list:
        if not self.is_logged_in():
            raise Exception('Not logged in!')

        start_num = ((page - 1) * per_page) + 1
        end_num = start_num + per_page - 1

        payload = {
            'Token': self._user['token'],
            'UserId': self._user['user_id'],
            'StartNum': start_num,
            'EndNum': end_num,
            'Classify': category,
            'FileSize': dimension,
            'FileType': file_type,
            'FileSort': sort,
            'Version': 12,
            'RefreshIndex': 0,
        }

        resp = requests.post(
            self._full_url('/GetCategoryFileListV2'),
            headers=self.HEADERS,
            json=payload,
            timeout=REQUESTS_TIMEOUT,
        )
        resp_json = resp.json()

        lst = []
        for item in resp_json['FileList']:
            lst.append(GalleryInfo(item))

        return lst

    def download(self, gallery_info: GalleryInfo) -> PixelBean:
        url = self._full_url(gallery_info.file_id, server=Server.FILE)
        resp = requests.get(
            url, headers=self.HEADERS, stream=True, timeout=REQUESTS_TIMEOUT
        )
        print(url)
        return PixelBeanDecoder.decode_stream(resp.raw)
