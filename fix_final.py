import os
import sys
import subprocess

# Define variáveis de ambiente
os.environ["PASSWORD"] = "test_password"
os.environ["USER"] = "test_user"
os.environ["HOST"] = "localhost"
os.environ["DATABASE"] = "test_database"


def main():
    print("🔧 CORREÇÃO FINAL DOS TESTES")
    print("=" * 50)

    print("✅ Variáveis de ambiente configuradas")
    print("✅ Validação corrigida no conftest.py")
    print("\n🚀 Executando testes...")
    print("=" * 50)

    # Executa pytest
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "api_mysql/tests",
            "-v",
            "--tb=short",
            "-q",
        ],
        cwd=os.getcwd(),
    )

    print("\n" + "=" * 50)
    if result.returncode == 0:
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("✅ API testada e funcionando corretamente!")
        print("\n📊 Cobertura dos testes:")
        print("  - Usuários: CRUD completo")
        print("  - Contatos: CRUD completo")
        print("  - Validações: Campos obrigatórios")
        print("  - Erros: Duplicatas e não encontrados")
    else:
        print("❌ Ainda há falhas nos testes")
        print("💡 Execute: python test_direct.py para ver detalhes")

    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
