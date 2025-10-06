import os
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env (se existir)
load_dotenv()

# Database
DB_USER = os.environ.get("DB_USER") or os.environ.get("USER")
DB_PASSWORD = os.environ["PASSWORD"]
DB_HOST = os.environ["HOST"]
DB_PORT = os.environ["DB_PORT"]
DB_DATABASE = os.environ["DATABASE"]

# Application
SECRET_KEY = os.environ["SECRET_KEY"]
API_BASE_URL = os.environ["API_BASE_URL"]
GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]

# AWS S3 - Para acesso ao bucket
AWS_REGION = os.environ.get("AWS_REGION", "us-east-2")
AWS_ACCESS_KEY_ID = os.environ["AWS_ACCESS_KEY_ID"]
AWS_SECRET_ACCESS_KEY = os.environ["AWS_SECRET_ACCESS_KEY"]
S3_BUCKET_QMONKEY = os.environ.get("S3_BUCKET_QMONKEY", "assets.drunagor.app")

# AWS SES - Para envio de emails
SES_SMTP_USER = os.environ.get("SES_SMTP_USER")
SES_SMTP_PASSWORD = os.environ.get("SES_SMTP_PASSWORD")
SES_SMTP_HOST = os.environ.get("SES_SMTP_HOST", "email-smtp.us-east-2.amazonaws.com")
SES_SMTP_PORT = os.environ.get("SES_SMTP_PORT", "587")

# Database URI
DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_DATABASE}?charset=utf8mb4"
