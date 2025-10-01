# resources/s3_images.py
from flask_restx import Namespace, Resource, reqparse
from werkzeug.datastructures import FileStorage
import boto3
from botocore.exceptions import ClientError
from uuid import uuid4
from io import BytesIO

from config import (
    AWS_REGION,
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    S3_BUCKET_QMONKEY,
)

# Namespace da API para agrupar as rotas de assets.
# (Eu centralizo tudo relacionado a S3 aqui em /assets)
assets = Namespace("assets", description="S3 assets")


# ---------- S3 client factory ----------
def s3_client():
    """
    Crio e retorno um cliente S3 configurado com minhas credenciais e região.
    Faço isso numa função para reutilizar e manter o código limpo.
    """
    return boto3.client(
        "s3",
        region_name=str(AWS_REGION),
        aws_access_key_id=str(AWS_ACCESS_KEY_ID),
        aws_secret_access_key=str(AWS_SECRET_ACCESS_KEY),
    )


# ---------- GET: list only image keys ----------
@assets.route("/images")
class Images(Resource):
    def get(self):
        """
        Lista SOMENTE os nomes (keys) das imagens existentes no bucket.
        Não retorno metadados, só um array 'items' com as chaves.
        - Eu filtro por extensões de imagem mais comuns.
        """
        client = s3_client()
        paginator = client.get_paginator("list_objects_v2")

        # Extensões que considero como imagem.
        # (Se eu precisar, ajusto essa lista depois.)
        image_exts = {"png", "jpg", "jpeg", "webp", "gif", "svg"}

        keys = []
        try:
            # Uso paginação para suportar muitos objetos no bucket.
            for page in paginator.paginate(Bucket=S3_BUCKET_QMONKEY):
                # Se não houver 'Contents', o page pode não ter objetos.
                for obj in page.get("Contents", []):
                    key = obj.get("Key")

                    # Ignoro "pastas" virtuais (terminam com '/')
                    if key.endswith("/"):
                        continue

                    # Filtro por extensão para garantir que só entro imagens.
                    ext = key.rsplit(".", 1)[-1].lower() if "." in key else ""
                    if ext in image_exts:
                        keys.append(key)
        except ClientError as e:
            # Em caso de erro de permissão/rede, retorno 500 com a mensagem da AWS.
            msg = e.response.get("Error", {}).get("Message", str(e))
            assets.abort(500, f"S3 access error: {msg}")

        # Ordeno para ter uma saída estável/alfabética.
        keys.sort()
        return {"items": keys}, 200

    # ---------- POST: upload PNG only (single 'file' field) ----------
    def post(self):
        """
        Faz upload de uma imagem PNG para o bucket.
        Regras que eu defini:
        - Só aceito um único campo 'file' no multipart/form-data.
        - A ÚNICA validação é: o Content-Type precisa ser 'image/png'.
        - Se o nome do arquivo vier vazio ou sem .png, eu gero um UUID .png.
        Retorno a 'key' gravada e o 'bucket' alvo.
        """
        parser = reqparse.RequestParser()
        parser.add_argument(
            "file",
            type=FileStorage,
            location="files",
            required=True,
            help="PNG file to upload (multipart/form-data, field name: file)",
        )
        args = parser.parse_args()
        file: FileStorage = args["file"]

        # Validação mínima pedida: confiro o MIME type informado.
        # (Se o cliente mentir no MIME, eu não bloqueio — essa foi a regra solicitada:
        # a única validação é Content-Type = image/png.)
        if (file.mimetype or "").lower() != "image/png":
            assets.abort(400, "Only PNG is allowed (Content-Type must be image/png).")

        # Se o filename não existir ou não terminar com .png,
        # eu forço um nome seguro via UUID.
        filename = (file.filename or "").strip()
        if not filename or not filename.lower().endswith(".png"):
            filename = f"{uuid4().hex}.png"

        # Leio o arquivo para memória e preparo um stream para o upload.
        try:
            raw = file.read()
            if not raw:
                assets.abort(400, "Empty file.")
            stream = BytesIO(raw)
        finally:
            # Por boa prática, tento reposicionar o ponteiro,
            # mesmo que não seja estritamente necessário após read().
            try:
                file.stream.seek(0)
            except Exception:
                pass

        # Subo sempre na raiz do bucket (sem prefixo).
        key = filename

        client = s3_client()
        try:
            client.upload_fileobj(
                Fileobj=stream,
                Bucket=S3_BUCKET_QMONKEY,
                Key=key,
                ExtraArgs={
                    # Gravo o Content-Type correto no S3.
                    "ContentType": "image/png",
                },
            )
        except ClientError as e:
            # Se algo falhar na AWS (permite, credencial, rede etc.), retorno 500.
            msg = e.response.get("Error", {}).get("Message", str(e))
            assets.abort(500, f"S3 upload error: {msg}")

        # Retorno o caminho gravado e o bucket para o cliente confirmar.
        return {"key": key, "bucket": S3_BUCKET_QMONKEY}, 201
