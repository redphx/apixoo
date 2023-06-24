from enum import Enum


class GalleryCategory(int, Enum):
    NEW = 0
    DEFAULT = 1
    # LED_TEXT = 2
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
    # PLANET = 19
    FOLLOW = 20
    # REVIEW_PHOTOS = 21
    # REVIEW_STOLEN_PHOTOS = 22
    # FILL_GAME = 29
    PIXEL_MATCH = 30  # Current event
    PLANT = 31
    ANIMAL = 32
    PERSON = 33
    EMOJI_2 = 34
    FOOD = 35
    # OTHERS = 36
    # REPORT_PHOTO = 254
    # CREATION_ALBUM = 255


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
    API = 'app.divoom-gz.com'
    FILE = 'f.divoom-gz.com'


class ApiEndpoint(str, Enum):
    GET_ALBUM_LIST = '/Discover/GetAlbumList'
    GET_ALBUM_FILES = '/Discover/GetAlbumImageList'
    GET_CATEGORY_FILES = '/GetCategoryFileListV2'
    GET_GALLERY_INFO = '/Cloud/GalleryInfo'
    USER_LOGIN = '/UserLogin'


class BaseDictInfo(dict):
    _KEYS_MAP = {}

    def __init__(self, info: dict):
        # Rename keys
        for key in self._KEYS_MAP:
            self.__dict__[self._KEYS_MAP[key]] = info.get(key)

        # Make this object JSON serializable
        dict.__init__(self, **self.__dict__)

    def __setattr__(self, name, value):
        raise Exception('%s object is read only!' % (type(self).__name__))


class AlbumInfo(BaseDictInfo):
    _KEYS_MAP = {
        'AlbumId': 'album_id',
        'AlbumName': 'album_name',
        'AlbumImageId': 'album_image_id',
        'AlbumBigImageId': 'album_big_image_id',
    }


class UserInfo(BaseDictInfo):
    _KEYS_MAP = {
        'UserId': 'user_id',
        'UserName': 'user_name',
    }


class GalleryInfo(BaseDictInfo):
    _KEYS_MAP = {
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
        super().__init__(info)

        # Parse user info
        self.__dict__['user'] = None
        if 'UserId' in info:
            self.__dict__['user'] = UserInfo(info)

        # Update dict
        dict.__init__(self, **self.__dict__)
