import os
import tempfile


class TestConfig:
    """Configuração para ambiente de testes."""

    # Configuração do banco para testes (SQLite em memória)
    TESTING = True
    WTF_CSRF_ENABLED = False

    # Usa SQLite para testes (mais rápido e não precisa de MySQL)
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Configurações de segurança para testes
    SECRET_KEY = "test-secret-key-not-for-production"

    # Desabilita logs durante testes
    SQLALCHEMY_ECHO = False


class ProductionConfig:
    """Configuração para produção (mantém MySQL)."""

    TESTING = False
    WTF_CSRF_ENABLED = True

    # Mantém configuração MySQL para produção
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", "mysql+mysqlconnector://user:password@localhost/database"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SECRET_KEY = os.getenv("SECRET_KEY", "your-production-secret-key")
    SQLALCHEMY_ECHO = False
