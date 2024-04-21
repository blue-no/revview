import os

appdata = os.getenv("APPDATA")
if appdata is not None:
    _settings_file = os.path.join(appdata, "RevView", "revview_settings")
else:
    _settings_file = os.path.join(".", "revview_settings")
_max_image_pixels = 1000000000
_max_image_size = (1080, 1920)
