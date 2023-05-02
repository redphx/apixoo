import hashlib
from enum import Enum

import requests

from .pixel_bean import PixelBean
from .pixel_bean_decoder import PixelBeanDecoder

REQUESTS_TIMEOUT = 10


class GalleryCategory(int, Enum):
    NEW = 0
    DEFAULT = 1
    LED_TEXT = 2
    CHARACTER = 3
    EMOJI = 4
    DAILY = 5
    NATURE = 6
    SYMBOL = 7
    PATTERN = 8
    CREATIVE = 9
    PHOTO = 12
    TOP = 14
    GADGET = 15
    BUSINESS = 16
    FESTIVAL = 17
    RECOMMEND = 18
    PLANET = 19
    FOLLOW = 20
    REVIEW_PHOTOS = 21
    REVIEW_STOLEN_PHOTOS = 22
    FILL_GAME = 29
    PIXEL_MATCH = 30
    PLANT = 31
    ANIMAL = 32
    PERSON = 33
    EMOJI_2 = 34
    FOOD = 35
    OTHERS = 36
    REPORT_PHOTO = 254
    CREATION_ALBUM = 255


class GalleryType(int, Enum):
    PICTURE = 0
    ANIMATION = 1
    MULTI_PICTURE = 2
    MULTI_ANIMATION = 3
    LED = 4
    ALL = 5
    SAND = 6
    DESIGN_HEAD_DEVICE = 101
    DESIGN_IMPORT = 103
    DESIGN_CHANNEL_DEVICE = 104


class GallerySorting(int, Enum):
    NEW_UPLOAD = 0
    MOST_LIKED = 1


class GalleryDimension(int, Enum):
    W16H16 = 1
    W32H32 = 2
    W64H64 = 4
    ALL = 15


class Server(str, Enum):
    API = 'https://app.divoom-gz.com'
    FILE = 'https://f.divoom-gz.com'


class UserInfo(dict):
    KEYS_MAP = {
        'UserId': 'user_id',
        'UserName': 'user_name',
    }

    def __init__(self, info: dict):
        # Rename keys
        for key in self.KEYS_MAP:
            self.__dict__[self.KEYS_MAP[key]] = info.get(key)

        # Make this object JSON serializable
        dict.__init__(self, **self.__dict__)

    def __setattr__(self, name, value):
        raise Exception('UserInfo object is read only!')


class GalleryInfo(dict):
    KEYS_MAP = {
        'Classify': 'category',
        'CommentCnt': 'total_comments',
        'Content': 'content',
        'CopyrightFlag': 'copyright_flag',
        'CountryISOCode': 'country_iso_code',
        'Date': 'date',
        'FileId': 'file_id',
        'FileName': 'file_name',
        'FileTagArray': 'file_tags',
        'FileType': 'file_type',
        'FileURL': 'file_url',
        'GalleryId': 'gallery_id',
        'LikeCnt': 'total_likes',
        'ShareCnt': 'total_shares',
        'WatchCnt': 'total_views',
        # 'AtList': [],
        # 'CheckConfirm': 2,
        # 'CommentUTC': 0,
        # 'FillGameIsFinish': 0,
        # 'FillGameScore': 0,
        # 'HideFlag': 0,
        # 'IsAddNew': 1,
        # 'IsAddRecommend': 0,
        # 'IsDel': 0,
        # 'IsFollow': 0,
        # 'IsLike': 0,
        # 'LayerFileId': '',
        # 'Level': 7,
        # 'LikeUTC': 1682836986,
        # 'MusicFileId': '',
        # 'OriginalGalleryId': 0,
        # 'PixelAmbId': '',
        # 'PixelAmbName': '',
        # 'PrivateFlag': 0,
        # 'RegionId': '55',
        # 'UserHeaderId': 'group1/M00/1B/BF/...',
    }

    def __init__(self, info: dict):
        # Rename keys
        for key in self.KEYS_MAP:
            self.__dict__[self.KEYS_MAP[key]] = info.get(key)

        # Parse user info
        self.__dict__['user'] = None
        if 'UserId' in info:
            self.__dict__['user'] = UserInfo(info)

        # Make this object JSON serializable
        dict.__init__(self, **self.__dict__)

    def __setattr__(self, name, value):
        raise Exception('GalleryInfo object is read only!')


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
