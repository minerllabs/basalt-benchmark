import io
import os
import uuid
from typing import IO

from fastapi import HTTPException

from config import Config
from .s3_uploads import s3_client
from .check_valid_mp4 import is_valid_mp4


def upload_file(file_content: bytes, verify: bool = True) -> str:
    """Upload a file to local or s3 storage

    :params file: A IO file object
    :returns: The filename
    """
    # Validate `mp4` file
    if verify:
        if not is_valid_mp4(file_content):
            raise HTTPException(422, "Invalid `.mp4` file")

    # Upload file
    target_filename = "{}.mp4".format(str(uuid.uuid4()))
    if Config.FILES_STORAGE_BACKEND == "local":
        # Save file to local directory
        target_filepath = os.path.join(Config.UPLOADS_DIR, target_filename)
        with open(target_filepath, "wb") as fp:
            fp.write(file_content)
    else:
        # Upload file to S3
        s3_client.upload_fileobj(file_obj=io.BytesIO(file_content), target_filename=target_filename)
    return target_filename
