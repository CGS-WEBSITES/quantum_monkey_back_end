import boto3
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Carregar credenciais
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
S3_BUCKET = os.environ.get("S3_BUCKET_QMONKEY", "assets.drunagor.app")

print("=" * 60)
print("TESTE DE ACESSO AWS S3")
print("=" * 60)
print(f"\n📦 Bucket: {S3_BUCKET}")
print(f"🌍 Região: {AWS_REGION}")

# Verificar se as credenciais foram carregadas
if not AWS_ACCESS_KEY_ID:
    print("\n❌ ERRO: AWS_ACCESS_KEY_ID não está definido!")
    print("Verifique seu arquivo .env")
    exit(1)

if not AWS_SECRET_ACCESS_KEY:
    print("\n❌ ERRO: AWS_SECRET_ACCESS_KEY não está definido!")
    print("Verifique seu arquivo .env")
    exit(1)

print(f"🔑 Access Key ID: {AWS_ACCESS_KEY_ID[:10]}...{AWS_ACCESS_KEY_ID[-4:]}")
print(f"🔐 Secret Key: {'*' * 20} (carregado)")

print("\n🔍 Verificando identidade IAM...")

try:
    sts = boto3.client(
        "sts",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )
    identity = sts.get_caller_identity()
    print(f"👤 Usuário IAM: {identity['Arn']}")
    print(f"📋 Account ID: {identity['Account']}")
except Exception as e:
    print(f"⚠️  Não foi possível verificar identidade: {str(e)}")


try:
    # Criar cliente S3
    print("\n🔄 Criando cliente S3...")
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION,
    )
    print("✅ Cliente S3 criado com sucesso!")

    # Teste 1: Verificar se o bucket existe
    print(f"\n🔄 Verificando existência do bucket '{S3_BUCKET}'...")
    try:
        s3_client.head_bucket(Bucket=S3_BUCKET)
        print(f"✅ Bucket '{S3_BUCKET}' existe e está acessível!")
    except Exception as e:
        print(f"❌ Erro ao acessar bucket: {str(e)}")
        print("\nPossíveis causas:")
        print("  1. Bucket não existe")
        print("  2. Região incorreta")
        print("  3. Sem permissão para acessar o bucket")
        exit(1)

    # Teste 2: Listar objetos
    print(f"\n🔄 Listando objetos no bucket...")
    response = s3_client.list_objects_v2(Bucket=S3_BUCKET, MaxKeys=10)

    key_count = response.get("KeyCount", 0)
    print(f"✅ Listagem bem-sucedida! Encontrados {key_count} objetos (max 10)")

    if "Contents" in response:
        print("\n📁 Primeiros arquivos encontrados:")
        for i, obj in enumerate(response["Contents"][:10], 1):
            size_kb = obj["Size"] / 1024
            print(f"  {i}. {obj['Key']} ({size_kb:.2f} KB)")
    else:
        print("\n⚠️  Bucket está vazio (sem objetos)")

    # Teste 3: Listar apenas imagens
    print(f"\n🔄 Filtrando apenas imagens...")
    image_extensions = (".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg")
    images = []

    paginator = s3_client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=S3_BUCKET):
        if "Contents" in page:
            for obj in page["Contents"]:
                if obj["Key"].lower().endswith(image_extensions):
                    images.append(obj["Key"])

    print(f"✅ Encontradas {len(images)} imagens no bucket")

    if images:
        print("\n🖼️  Primeiras imagens:")
        for i, img in enumerate(images[:10], 1):
            print(f"  {i}. {img}")

    print("\n" + "=" * 60)
    print("✅ TODOS OS TESTES PASSARAM!")
    print("=" * 60)
    print("\n✨ Suas credenciais AWS estão funcionando corretamente!")
    print(f"✨ O bucket '{S3_BUCKET}' está acessível!")

except Exception as e:
    print("\n" + "=" * 60)
    print("❌ ERRO NO TESTE")
    print("=" * 60)
    print(f"\nTipo do erro: {type(e).__name__}")
    print(f"Mensagem: {str(e)}")

    # Dicas de solução
    print("\n💡 Possíveis soluções:")
    if "AccessDenied" in str(e):
        print("  1. Verifique as permissões IAM do usuário")
        print("  2. Confirme se as credenciais são as corretas")
        print("  3. Verifique se o bucket policy permite acesso")
    elif "NoSuchBucket" in str(e):
        print("  1. Verifique o nome do bucket no .env")
        print("  2. Confirme a região do bucket")
    elif "InvalidAccessKeyId" in str(e):
        print("  1. Verifique se o AWS_ACCESS_KEY_ID está correto")
        print("  2. Confirme se a chave não foi revogada")
    elif "SignatureDoesNotMatch" in str(e):
        print("  1. Verifique se o AWS_SECRET_ACCESS_KEY está correto")
        print("  2. Confirme se não há espaços extras nas credenciais")
    else:
        print("  1. Verifique sua conexão com a internet")
        print("  2. Confirme se todas as variáveis do .env estão corretas")
        print("  3. Tente executar novamente")

    exit(1)
