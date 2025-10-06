import os
import sys

# Define as variáveis de ambiente necessárias
os.environ["PASSWORD"] = "test_password"
os.environ["USER"] = "test_user"
os.environ["HOST"] = "localhost"
os.environ["DATABASE"] = "test_database"

# Executa pytest diretamente
if __name__ == "__main__":
    print("🧪 EXECUTANDO TESTE DIRETO")
    print("=" * 40)

    # Verifica se pytest está disponível
    try:
        import pytest

        print("✅ Pytest disponível")
    except ImportError:
        print("❌ Pytest não encontrado. Instale com: pip install pytest")
        sys.exit(1)

    # Executa os testes
    print("\n🚀 Executando testes...")
    print("=" * 40)

    # Comando pytest
    exit_code = pytest.main(["api_mysql/tests", "-v", "--tb=short"])

    print("\n" + "=" * 40)
    if exit_code == 0:
        print("🎉 TODOS OS TESTES PASSARAM!")
    else:
        print("❌ ALGUNS TESTES FALHARAM")
        print("💡 Verifique as mensagens de erro acima")

    sys.exit(exit_code)
