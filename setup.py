try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

long_desc = open("README.md").read()
required = ['requests']

setup(
    name='APIxoo',
    version="0.3.1",
    author="redphx",
    license="MIT",
    url="https://github.com/redphx/apixoo",
    download_url="https://github.com/redphx/apixoo",
    long_description=long_desc,
    long_description_content_type="text/markdown",
    description="Python wrapper for Divoom Pixoo server API",
    packages=[
        "apixoo"
    ],
    include_package_data=True,
    install_requires=required,
    platforms="any",
    keywords=[
        "apixoo",
        "divoom",
        "pixoo",
        "pixoo64"
    ],
    classifiers=[
        "Intended Audience :: Developers",
        "Topic :: Software Development",
        "Programming Language :: Python"
    ],
    python_requires=">3.6",
)
