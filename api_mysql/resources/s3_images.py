from flask_restx import Namespace, Resource, fields
from werkzeug.datastructures import FileStorage
import boto3
from botocore.exceptions import ClientError
from uuid import uuid4
from io import BytesIO
from urllib.parse import quote

from config import (
    AWS_S3_REGION,
    AWS_S3_ACCESS_KEY_ID,
    AWS_S3_SECRET_ACCESS_KEY,
    S3_BUCKET,
)

assets = Namespace("assets", description="S3 assets operations")

BUCKET_NAME = S3_BUCKET or "druna-assets"

image_model = assets.model(
    "Image",
    {
        "id": fields.String(description="Unique identifier (S3 key)"),
        "name": fields.String(description="File name"),
        "url": fields.String(description="Public or presigned URL"),
        "key": fields.String(description="S3 object key"),
    },
)

upload_response_model = assets.model(
    "UploadResponse",
    {
        "id": fields.String(description="Unique identifier"),
        "key": fields.String(description="S3 object key"),
        "name": fields.String(description="File name"),
        "url": fields.String(description="Access URL"),
        "bucket": fields.String(description="S3 bucket name"),
    },
)

error_model = assets.model(
    "Error", {"message": fields.String(description="Error message")}
)

upload_parser = assets.parser()
upload_parser.add_argument(
    "input",
    type=FileStorage,
    location="files",
    required=True,
    help="Image file to upload (multipart/form-data)",
)


def get_s3_client():
    return boto3.client(
        "s3",
        region_name=str(AWS_S3_REGION) if AWS_S3_REGION else "us-east-2",
        aws_access_key_id=str(AWS_S3_ACCESS_KEY_ID) if AWS_S3_ACCESS_KEY_ID else None,
        aws_secret_access_key=(
            str(AWS_S3_SECRET_ACCESS_KEY) if AWS_S3_SECRET_ACCESS_KEY else None
        ),
    )


def get_public_url(key):
    encoded_key = quote(key, safe="/")
    return f"https://{BUCKET_NAME}.s3.us-east-2.amazonaws.com/{encoded_key}"


@assets.route("/images")
class Images(Resource):

    @assets.doc("list_images")
    @assets.response(200, "Success")
    @assets.response(500, "S3 Error", error_model)
    def get(self):
        client = get_s3_client()
        paginator = client.get_paginator("list_objects_v2")

        image_exts = {"png", "jpg", "jpeg", "webp", "gif", "svg"}

        images = []
        try:
            for page in paginator.paginate(Bucket=BUCKET_NAME):
                for obj in page.get("Contents", []):
                    key = obj.get("Key", "")

                    if key.endswith("/"):
                        continue

                    ext = key.rsplit(".", 1)[-1].lower() if "." in key else ""
                    if ext not in image_exts:
                        continue

                    name = key.split("/")[-1] if "/" in key else key

                    url = get_public_url(key)

                    images.append(
                        {
                            "id": key,
                            "name": name,
                            "key": key,
                            "url": url,
                        }
                    )

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            error_msg = e.response.get("Error", {}).get("Message", str(e))

            if error_code == "AccessDenied":
                assets.abort(
                    500,
                    f"Acesso negado ao S3. Verifique as permissões IAM para o bucket '{BUCKET_NAME}'. "
                    f"Erro: {error_msg}",
                )
            else:
                assets.abort(500, f"Erro ao acessar S3: {error_msg}")

        images.sort(key=lambda x: x["name"].lower())

        return images, 200

    @assets.doc("upload_image")
    @assets.expect(upload_parser)
    @assets.marshal_with(upload_response_model, code=201)
    @assets.response(201, "Upload successful", upload_response_model)
    @assets.response(400, "Bad request", error_model)
    @assets.response(500, "S3 Error", error_model)
    def post(self):
        args = upload_parser.parse_args()
        file = args["input"]

        if not file:
            assets.abort(400, "Nenhum arquivo fornecido")

        mimetype = (file.mimetype or "").lower()
        valid_mimes = [
            "image/png",
            "image/jpeg",
            "image/jpg",
            "image/webp",
            "image/gif",
        ]

        if mimetype not in valid_mimes:
            assets.abort(
                400,
                f"Tipo de arquivo não suportado: {mimetype}. Use PNG, JPEG, WebP ou GIF.",
            )

        original_filename = (file.filename or "").strip()
        if not original_filename:
            ext = mimetype.split("/")[-1] if "/" in mimetype else "png"
            original_filename = f"{uuid4().hex}.{ext}"

        try:
            raw = file.read()
            if not raw:
                assets.abort(400, "Arquivo vazio")
            stream = BytesIO(raw)
        except Exception as e:
            assets.abort(400, f"Erro ao ler arquivo: {str(e)}")
        finally:
            try:
                file.stream.seek(0)
            except Exception:
                pass

        key = original_filename

        client = get_s3_client()
        try:
            client.upload_fileobj(
                Fileobj=stream,
                Bucket=BUCKET_NAME,
                Key=key,
                ExtraArgs={
                    "ContentType": mimetype,
                },
            )
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            error_msg = e.response.get("Error", {}).get("Message", str(e))

            if error_code == "AccessDenied":
                assets.abort(
                    500,
                    f"Acesso negado para upload. Verifique as permissões IAM. Erro: {error_msg}",
                )
            else:
                assets.abort(500, f"Erro no upload para S3: {error_msg}")

        url = get_public_url(key)

        return {
            "id": key,
            "key": key,
            "name": original_filename,
            "url": url,
            "bucket": BUCKET_NAME,
        }, 201


@assets.route("/images/<path:key>")
@assets.param("key", "The S3 object key")
class ImageDetail(Resource):

    @assets.doc("get_image_url")
    @assets.response(200, "Success")
    @assets.response(404, "Image not found")
    def get(self, key):
        client = get_s3_client()

        try:
            client.head_object(Bucket=BUCKET_NAME, Key=key)

            name = key.split("/")[-1] if "/" in key else key
            url = get_public_url(key)

            return {
                "id": key,
                "key": key,
                "name": name,
                "url": url,
            }, 200

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code in ["404", "NoSuchKey"]:
                assets.abort(404, f"Imagem não encontrada: {key}")
            else:
                error_msg = e.response.get("Error", {}).get("Message", str(e))
                assets.abort(500, f"Erro S3: {error_msg}")

    @assets.doc("delete_image")
    @assets.response(204, "Deleted successfully")
    @assets.response(404, "Image not found")
    def delete(self, key):
        client = get_s3_client()

        try:
            client.head_object(Bucket=BUCKET_NAME, Key=key)
            client.delete_object(Bucket=BUCKET_NAME, Key=key)
            return "", 204

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code in ["404", "NoSuchKey"]:
                assets.abort(404, f"Imagem não encontrada: {key}")
            else:
                error_msg = e.response.get("Error", {}).get("Message", str(e))
                assets.abort(500, f"Erro ao deletar: {error_msg}")
