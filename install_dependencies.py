import subprocess
import sys
import os


def run_command(command, description):
    """Executa um comando e mostra o resultado."""
    print(f"\n{'='*50}")
    print(f"EXECUTANDO: {description}")
    print(f"COMANDO: {command}")
    print(f"{'='*50}")

    result = subprocess.run(command, shell=True, text=True)
    return result.returncode == 0


def check_virtual_env():
    """Verifica se está em um ambiente virtual."""
    if hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    ):
        print("✅ Ambiente virtual detectado")
        return True
    else:
        print("⚠️  AVISO: Não foi detectado ambiente virtual ativo")
        print("   Recomendamos usar um ambiente virtual:")
        print("   python -m venv venv")
        print("   source venv/bin/activate  # Linux/Mac")
        print("   venv\\Scripts\\activate     # Windows")
        return False


def main():
    """Função principal."""
    print("🔧 INSTALADOR DE DEPENDÊNCIAS DA API")

    # Verifica ambiente virtual
    check_virtual_env()

    # Lista de dependências
    dependencies = [
        # Principais para a API
        "flask",
        "flask-restx",
        "flask-sqlalchemy",
        # Para testes
        "pytest",
        "pytest-flask",
        "pytest-cov",
        "requests",
        "python-dotenv",
        # Opcional para MySQL (se precisar)
        "mysql-connector-python",
    ]

    print(f"\n📦 INSTALANDO {len(dependencies)} DEPENDÊNCIAS...")

    # Atualiza pip primeiro
    print("\n🔄 Atualizando pip...")
    run_command("pip install --upgrade pip", "Atualização do pip")

    # Instala cada dependência
    failed_packages = []
    for package in dependencies:
        print(f"\n📦 Instalando {package}...")
        success = run_command(f"pip install {package}", f"Instalação do {package}")
        if not success:
            failed_packages.append(package)
            print(f"❌ Falha ao instalar {package}")
        else:
            print(f"✅ {package} instalado com sucesso")

    # Relatório final
    print(f"\n{'='*50}")
    print("📊 RELATÓRIO DE INSTALAÇÃO")
    print(f"{'='*50}")

    if not failed_packages:
        print("🎉 TODAS AS DEPENDÊNCIAS FORAM INSTALADAS COM SUCESSO!")
        print("\n✅ Próximos passos:")
        print("   1. python check_dependencies.py  # Verificar instalação")
        print("   2. python run_tests.py           # Executar testes")
    else:
        print(f"⚠️  {len(failed_packages)} dependência(s) falharam:")
        for package in failed_packages:
            print(f"   - {package}")
        print("\n🔧 Tente instalar manualmente:")
        for package in failed_packages:
            print(f"   pip install {package}")

    # Verifica se os arquivos de configuração existem
    print(f"\n🔍 VERIFICANDO ARQUIVOS DE CONFIGURAÇÃO...")

    required_files = [
        "api_mysql/tests/conftest.py",
        "api_mysql/tests/test_config.py",
        "api_mysql/tests/test_users.py",
        "api_mysql/tests/test_contacts.py",
        "pytest.ini",
    ]

    missing_files = []
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path}")
            missing_files.append(file_path)

    if missing_files:
        print(f"\n⚠️  {len(missing_files)} arquivo(s) de configuração estão faltando.")
        print("   Certifique-se de criar todos os arquivos conforme o guia.")
    else:
        print("\n✅ Todos os arquivos de configuração estão presentes!")


if __name__ == "__main__":
    main()
