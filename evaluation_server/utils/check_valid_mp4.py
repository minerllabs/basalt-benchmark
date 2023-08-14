import copy
from typing.io import IO
import filetype


def is_valid_mp4(file_content: bytes) -> bool:
    """Checks if a file is valid `mp4`

    :params file: A BinaryIO file object
    """
    file_type = filetype.guess(file_content)
    if file_type is None or file_type.mime != "video/mp4":
        return False

    return True
