import boto3
import os

bucket = os.environ.get('S3_BUCKET') or 'druna-assets'
region = os.environ.get('AWS_S3_REGION') or 'us-east-2'
key_id = os.environ.get('AWS_S3_ACCESS_KEY_ID')
secret = os.environ.get('AWS_S3_SECRET_ACCESS_KEY')

print("Uploading cgs_logo.jpg to bucket:", bucket)

s3 = boto3.client(
    's3',
    region_name=region,
    aws_access_key_id=key_id,
    aws_secret_access_key=secret
)

s3.upload_file('cgs_logo.jpg', bucket, 'cgs_logo.jpg', ExtraArgs={'ContentType': 'image/jpeg'})
print("Upload complete!")
