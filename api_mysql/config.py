import os

user = os.environ["USER"]
password = os.environ["PASSWORD"]
host = os.environ["HOST"]
port = os.environ["DB_PORT"]
database = os.environ["DATABASE"]

DATABASE_URI = (
    f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset=utf8mb4"
)

SECRET_KEY = os.environ["SECRET_KEY"]
GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]
API_BASE_URL = os.environ["API_BASE_URL"]

# AWS S3 (assets)
AWS_S3_REGION = os.environ.get("AWS_S3_REGION")
AWS_S3_ACCESS_KEY_ID = os.environ.get("AWS_S3_ACCESS_KEY_ID")
AWS_S3_SECRET_ACCESS_KEY = os.environ.get("AWS_S3_SECRET_ACCESS_KEY")
S3_BUCKET = os.environ.get("S3_BUCKET")

# AWS SES (@wearecgs.com)
AWS_REGION = os.environ["AWS_REGION"]
AWS_ACCESS_KEY_ID = os.environ["AWS_ACCESS_KEY_ID"]
AWS_SECRET_ACCESS_KEY = os.environ["AWS_SECRET_ACCESS_KEY"]
