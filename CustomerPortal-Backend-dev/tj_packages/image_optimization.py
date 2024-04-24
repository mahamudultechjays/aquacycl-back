import io

from django.core.files.uploadedfile import InMemoryUploadedFile
from PIL import Image


def get_optimized_image(
    image: object, image_name: str, quality: int, ext: str, size=None
):
    i = Image.open(image)
    image_mode = i.mode  # to find this image grayscale or RGBA
    i = i.convert(image_mode)
    thumb_io = io.BytesIO()
    if size:
        i.thumbnail(size)
    i.save(thumb_io, format="png", quality=quality)
    image = InMemoryUploadedFile(
        thumb_io, None, image_name, ext, thumb_io.tell(), None
    )
    return image
