from typing import BinaryIO
import boto3
from config import Config


class S3Client:
    def __init__(self):
        self.client = boto3.client('s3', aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
                                   aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
                                   endpoint_url=Config.AWS_S3_ENDPOINT_URL,
                                   region_name=Config.AWS_S3_REGION_NAME)

    def upload_file(self, file_path: str, target_filename: str) -> None:
        """Upload File from disk to S3

        :params file_path: Path to file
        :params target_filename: Filename to be used for upload
        """
        self.client.upload_file(file_path, Config.AWS_S3_BUCKET_NAME, Config.AWS_S3_BUCKET_KEY_PREFIX + target_filename)

    def upload_fileobj(self, file_obj: BinaryIO, target_filename: str) -> None:
        """Upload File object to S3

        :params file_obj: A BinaryIO file object
        :params target_filename: Filename to be used for upload
        """
        self.client.upload_fileobj(file_obj, Config.AWS_S3_BUCKET_NAME,
                                   Config.AWS_S3_BUCKET_KEY_PREFIX + target_filename)

    def get_presigned_url(self, filename: str) -> str:
        """Get presigned URL of an object from S3 bucket

        :params filename: Filename of object
        """
        return self.client.generate_presigned_url('get_object',
                                                  Params={'Bucket': Config.AWS_S3_BUCKET_NAME,
                                                          'Key': Config.AWS_S3_BUCKET_KEY_PREFIX + filename},
                                                  ExpiresIn=Config.MATCH_EXPIRY_TIME_MINS * 60)


s3_client = S3Client()
