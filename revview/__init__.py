# __init__.py
from PIL import Image

from revview._const import _max_image_pixels

Image.MAX_IMAGE_PIXELS = _max_image_pixels
