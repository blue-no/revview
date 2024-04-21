import os

__cwd = os.getcwd()
__appdata = os.getenv("APPDATA")
if __appdata is not None:
    _settings_file = os.path.join(__appdata, "RevView", "revview_settings")
else:
    _settings_file = os.path.join(__cwd, "revview_settings")

__userproflie = os.getenv("USERPROFILE")
if __userproflie is not None:
    _file_dialog_root = os.path.join(__userproflie, "Desktop")
else:
    _file_dialog_root = os.path.join(__cwd)

_max_image_pixels = 1000000000
_max_image_size = (1080, 1920)
