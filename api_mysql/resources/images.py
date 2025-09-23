from flask_restx import Resource, Namespace, reqparse, fields, marshal
from flask_jwt_extended import jwt_required
from sql_alchemy import MySQLConnection
from utils import boolean_string
from werkzeug.datastructures import FileStorage
import boto3
import os

images = Namespace("Images", "Images related Endpoints")

@images.route("/upload")
class FileUpload(Resource):
    parser = reqparse.RequestParser()

    parser.add_argument(
        "file",
        type=FileStorage,
        location="files",
        required=True,
        help="File is required.",
    )

    @images.expect(parser, validate=True)
    def post(self):
        args = self.parser.parse_args()
        uploaded_file = args["file"]  # This is a FileStorage object

        # Optionally generate a unique key for your file
        key = f"User/{int(round(__import__('time').time() * 1000))}_{uploaded_file.filename}"

        try:
            s3.upload_fileobj(
                uploaded_file,
                BUCKET,
                key,
                ExtraArgs={"ContentType": uploaded_file.content_type},
            )
        except Exception as e:
            return {"message": "Error uploading file", "error": str(e)}, 500

        return {"message": "File uploaded successfully", "image_key": key}, 201
