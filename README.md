[![PyPI](https://img.shields.io/pypi/v/APIxoo?label=PyPI%20Package)](https://pypi.org/project/APIxoo/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

# APIxoo
Python package to interact with Divoom Pixoo app's server.  
Unlike other packages, this one will only focus on interacting with Divoom Pixoo's server.  
  
For ESP32/Arduino, check [redphx/DivoomClient](https://github.com/redphx/DivoomClient). 

## Features
- [x] Login
- [x] Decode Divoom's animation formats to GIFs (16x16, 32x32, 64x64).  
- [x] Get animation by ID
- [x] Get animations by Category
- [x] Get animations by Album
- [ ] Get animations by User
- [ ] Search animations & users
- [ ] Like/Dislike animation
- [ ] Comment on animation
- [ ] Upload animations

## Install
```
pip install APIxoo
```

## Example
```python
from apixoo import APIxoo, GalleryCategory, GalleryDimension

# Divoom account
EMAIL = 'em@il.com'
MD5_PASSWORD = 'deadc0ffee...'

# Also accept password string with "password='password'"
api = APIxoo(EMAIL, md5_password=MD5_PASSWORD)
status = api.log_in()
if not status:
    print('Login error!')
else:
    files = api.get_category_files(
        GalleryCategory.RECOMMEND,
        dimension=GalleryDimension.W64H64,
        page=1,
        per_page=20,
    )

    for info in files:
        print(info)
        pixel_bean = api.download(info)
        if pixel_bean:
            pixel_bean.save_to_gif(f'{info.gallery_id}.gif', scale=5)
```

*To be updated...*  
