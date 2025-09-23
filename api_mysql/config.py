import os

user = os.environ["USER"]
password = os.environ["PASSWORD"]
host = os.environ["HOST"]
port = os.environ["DB_PORT"]
database = os.environ["DATABASE"]
SECRET_KEY = os.environ["SECRET_KEY"]
AWS_REGION = os.environ["AWS_REGION"]
AWS_ACCESS_KEY_ID = os.environ["AWS_ACCESS_KEY_ID"]
AWS_SECRET_ACCESS_KEY = os.environ["AWS_SECRET_ACCESS_KEY"]
GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]
API_BASE_URL = os.environ["API_BASE_URL"]

DATABASE_URI = (
    f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset=utf8mb4"
)
