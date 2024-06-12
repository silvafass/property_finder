import cv2
import numpy as np
from typing import List


def vertically_concat_images(
    images: List[bytes], interpolation: int = cv2.INTER_CUBIC
) -> bytes:
    images = [np.fromstring(image, np.uint8) for image in images]
    images: List[cv2.typing.MatLike] = [
        cv2.imdecode(image, cv2.IMREAD_COLOR) for image in images
    ]
    minimum_width = min(image.shape[1] for image in images)
    resized_images = [
        cv2.resize(
            image,
            (
                minimum_width,
                int(image.shape[0] * minimum_width / image.shape[1]),
            ),
            interpolation=interpolation,
        )
        for image in images
    ]
    concat_image = cv2.vconcat(resized_images)
    _, concat_image_in_bytes = cv2.imencode(
        ".jpg", concat_image, [cv2.IMWRITE_JPEG_QUALITY, 50]
    )
    return concat_image_in_bytes.tobytes()
