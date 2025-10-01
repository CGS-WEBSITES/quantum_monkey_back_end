# resources/s3_images.py
from flask_restx import Namespace, Resource, reqparse
import boto3
from botocore.exceptions import ClientError
from config import (
    AWS_REGION,
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    S3_BUCKET_QMONKEY,
)

assets = Namespace("assets", description="S3 assets")

list_parser = reqparse.RequestParser()
list_parser.add_argument(
    "prefix",
    required=False,
    default="",
    help="Filter by prefix (folder). E.g., '' or 'icons/'",
)
list_parser.add_argument(
    "max_keys",
    type=int,
    required=False,
    default=1000,
    help="Max keys per page (default 1000)",
)
list_parser.add_argument(
    "extensions",
    required=False,
    default="png,jpg,jpeg,webp,gif,svg",
    help="Allowed extensions, comma-separated",
)


def s3_client():
    return boto3.client(
        "s3",
        region_name=str(AWS_REGION),
        aws_access_key_id=str(AWS_ACCESS_KEY_ID),
        aws_secret_access_key=str(AWS_SECRET_ACCESS_KEY),
    )


@assets.route("/images")
class ImagesList(Resource):
    @assets.doc(
        params={
            "prefix": "List only keys under this prefix (folder).",
            "max_keys": "Max items per page (default 1000).",
            "extensions": "Allowed extensions: png,jpg,jpeg,webp,gif,svg.",
        }
    )
    def get(self):
        """
        Return ONLY the existing image keys from the bucket.
        Response shape: {"items": ["btn-corebox.png", "icons/thing.png", ...]}
        """
        args = list_parser.parse_args()
        prefix = args.get("prefix") or ""
        max_keys = args.get("max_keys") or 1000
        allowed_exts = {
            e.strip().lower()
            for e in (args.get("extensions") or "").split(",")
            if e.strip()
        }

        client = s3_client()
        paginator = client.get_paginator("list_objects_v2")

        keys = []
        try:
            for page in paginator.paginate(
                Bucket=S3_BUCKET_QMONKEY,
                Prefix=prefix,
                PaginationConfig={"PageSize": max_keys},
            ):
                for obj in page.get("Contents", []):
                    key = obj.get("Key")
                    if key.endswith("/"):  # skip "folders"
                        continue
                    if allowed_exts:
                        ext = key.rsplit(".", 1)[-1].lower() if "." in key else ""
                        if ext not in allowed_exts:
                            continue
                    keys.append(key)
        except ClientError as e:
            msg = e.response.get("Error", {}).get("Message", str(e))
            assets.abort(500, f"S3 access error: {msg}")

        # Sort for stable output (optional)
        keys.sort()
        return {"items": keys}, 200
