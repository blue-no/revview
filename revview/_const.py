# _const.py
import os

__settings_name = "revview_settings.json"
__app_name = "RevView"
__cwd = os.getcwd()
__appdata = os.getenv("APPDATA")

if __appdata is not None:
    _settings_file = os.path.join(__appdata, __app_name, __settings_name)
else:
    _settings_file = os.path.join(__cwd, __settings_name)

_max_image_pixels = 1000000000
_max_image_size = (1080, 1920)
