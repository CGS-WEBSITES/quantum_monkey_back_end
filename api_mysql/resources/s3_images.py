from flask_restx import Namespace, Resource, fields
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

# Namespace da API
assets = Namespace("assets", description="S3 assets operations")

# ---------- Modelos para documentação Swagger ----------
image_list_model = assets.model(
    "ImageList", {"items": fields.List(fields.String, description="List of image keys")}
)

upload_response_model = assets.model(
    "UploadResponse",
    {
        "key": fields.String(description="S3 object key"),
        "bucket": fields.String(description="S3 bucket name"),
    },
)

error_model = assets.model(
    "Error", {"message": fields.String(description="Error message")}
)

# ---------- Parser para upload ----------
upload_parser = assets.parser()
upload_parser.add_argument(
    "input",
    type=FileStorage,
    location="files",
    required=True,
    help="PNG image file to upload (multipart/form-data)",
)


# ---------- S3 client factory ----------
def s3_client():
    """Create and return a configured S3 client"""
    return boto3.client(
        "s3",
        region_name=str(AWS_REGION),
        aws_access_key_id=str(AWS_ACCESS_KEY_ID),
        aws_secret_access_key=str(AWS_SECRET_ACCESS_KEY),
    )


@assets.route("/images")
class Images(Resource):

    @assets.doc("list_images")
    @assets.marshal_with(image_list_model)
    @assets.response(200, "Success", image_list_model)
    @assets.response(500, "S3 Error", error_model)
    def get(self):
        """List all image keys from S3 bucket"""
        client = s3_client()
        paginator = client.get_paginator("list_objects_v2")

        # Extensões de imagem suportadas
        image_exts = {"png", "jpg", "jpeg", "webp", "gif", "svg"}

        keys = []
        try:
            # Paginação para suportar muitos objetos
            for page in paginator.paginate(Bucket=S3_BUCKET_QMONKEY):
                for obj in page.get("Contents", []):
                    key = obj.get("Key")

                    # Ignora "pastas" virtuais
                    if key.endswith("/"):
                        continue

                    # Filtra por extensão de imagem
                    ext = key.rsplit(".", 1)[-1].lower() if "." in key else ""
                    if ext in image_exts:
                        keys.append(key)

        except ClientError as e:
            msg = e.response.get("Error", {}).get("Message", str(e))
            assets.abort(500, f"S3 access error: {msg}")

        keys.sort()
        return {"items": keys}, 200

    @assets.doc("upload_image")
    @assets.expect(upload_parser)
    @assets.marshal_with(upload_response_model, code=201)
    @assets.response(201, "Upload successful", upload_response_model)
    @assets.response(400, "Bad request", error_model)
    @assets.response(500, "S3 Error", error_model)
    def post(self):
        """Upload a PNG image to S3 bucket"""
        args = upload_parser.parse_args()
        file = args["input"]

        # Validação do tipo MIME
        if not file:
            assets.abort(400, "No file provided")

        if (file.mimetype or "").lower() != "image/png":
            assets.abort(400, "Only PNG is allowed (Content-Type must be image/png)")

        # Define o nome do arquivo
        filename = (file.filename or "").strip()
        if not filename or not filename.lower().endswith(".png"):
            filename = f"{uuid4().hex}.png"

        # Lê o arquivo para memória
        try:
            raw = file.read()
            if not raw:
                assets.abort(400, "Empty file")
            stream = BytesIO(raw)
        finally:
            # Reposiciona o ponteiro
            try:
                file.stream.seek(0)
            except Exception:
                pass

        # Define a chave no S3
        key = filename

        # Upload para o S3
        client = s3_client()
        try:
            client.upload_fileobj(
                Fileobj=stream,
                Bucket=S3_BUCKET_QMONKEY,
                Key=key,
                ExtraArgs={
                    "ContentType": "image/png",
                    # Opcional: tornar público
                    # "ACL": "public-read"
                },
            )
        except ClientError as e:
            msg = e.response.get("Error", {}).get("Message", str(e))
            assets.abort(500, f"S3 upload error: {msg}")

        return {"key": key, "bucket": S3_BUCKET_QMONKEY}, 201


# ---------- Rota adicional para obter URL de um objeto ----------
@assets.route("/images/<string:key>")
@assets.param("key", "The S3 object key")
class ImageDetail(Resource):

    @assets.doc("get_image_url")
    @assets.response(200, "Success")
    @assets.response(404, "Image not found")
    def get(self, key):
        """Get presigned URL for a specific image"""
        client = s3_client()

        try:
            # Verifica se o objeto existe
            client.head_object(Bucket=S3_BUCKET_QMONKEY, Key=key)

            # Gera URL pré-assinada (válida por 1 hora)
            url = client.generate_presigned_url(
                "get_object",
                Params={"Bucket": S3_BUCKET_QMONKEY, "Key": key},
                ExpiresIn=3600,
            )

            return {"url": url, "key": key, "expires_in": 3600}, 200

        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                assets.abort(404, f"Image not found: {key}")
            else:
                msg = e.response.get("Error", {}).get("Message", str(e))
                assets.abort(500, f"S3 error: {msg}")

    @assets.doc("delete_image")
    @assets.response(204, "Deleted successfully")
    @assets.response(404, "Image not found")
    def delete(self, key):
        """Delete an image from S3"""
        client = s3_client()

        try:
            client.delete_object(Bucket=S3_BUCKET_QMONKEY, Key=key)
            return "", 204

        except ClientError as e:
            msg = e.response.get("Error", {}).get("Message", str(e))
            assets.abort(500, f"S3 delete error: {msg}")
