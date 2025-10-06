import os
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env (se existir)
load_dotenv()

# Database - usando nomes mais específicos
DB_USER = os.environ.get("DB_USER") or os.environ.get("USER")
DB_PASSWORD = os.environ["PASSWORD"]
DB_HOST = os.environ["HOST"]
DB_PORT = os.environ["DB_PORT"]
DB_DATABASE = os.environ["DATABASE"]

# Application
SECRET_KEY = os.environ["SECRET_KEY"]
API_BASE_URL = os.environ["API_BASE_URL"]

# AWS
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY_ID = os.environ["AWS_ACCESS_KEY_ID"]
AWS_SECRET_ACCESS_KEY = os.environ["AWS_SECRET_ACCESS_KEY"]
S3_BUCKET_QMONKEY = os.environ.get("S3_BUCKET_QMONKEY", "assets.drunagor.app")

# Google
GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]

# Database URI
DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_DATABASE}?charset=utf8mb4"

# Validação (opcional mas recomendado)
required_vars = [
    "PASSWORD",
    "HOST",
    "DB_PORT",
    "DATABASE",
    "SECRET_KEY",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "GOOGLE_API_KEY",
    "API_BASE_URL",
]

missing_vars = [var for var in required_vars if not os.environ.get(var)]
if missing_vars:
    raise EnvironmentError(
        f"Variáveis de ambiente obrigatórias não encontradas: {', '.join(missing_vars)}"
    )
