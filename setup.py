from distutils.core import setup
import py2exe
setup(
    name="Youtube Downloader",
    version='2.1',
    author="Danish Khan",
    author_email="danishex07@gmail.com",
    windows = [{'script': "Youtube.py" , 'icon_resources': [(0, 'Youtube.ico')]}],
    zipfile = None,
)
