import boto3
from botocore.exceptions import ClientError
from config import AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, API_BASE_URL
from botocore.config import Config
from models.users import UserModel


config = Config(signature_version="s3v4")


def send(recipient, subject, body):
    sender = "no-reply@drunagor.app"

    ses_client = boto3.client(
        "ses",
        region_name=str(AWS_REGION),
        aws_access_key_id=str(AWS_ACCESS_KEY_ID),
        aws_secret_access_key=str(AWS_SECRET_ACCESS_KEY),
    )

    mensagem = {
        "Subject": {"Data": subject},
        "Body": {"Html": {"Data": body}},
    }

    try:
        response = ses_client.send_email(
            Source=sender,
            Destination={"ToAddresses": [recipient]},
            Message=mensagem,
        )
        return {"message": "Email sent successfully", "response": response}
    except ClientError as e:
        error_message = e.response["Error"]["Message"]
        print(f"Error sending email: {error_message}")
        return {"error": error_message}, 500


def send_store_verification_email(store_data):
    recipient = "james@wearecgs.com"
    sender = "store-verify@drunagor.app"
    subject = f"New Store for Verification: {
        store_data.get('name', 'ID: ' + str(store_data.get('pk')))
    }"

    verification_link = f"{API_BASE_URL}/stores/{store_data.get(
        'stores_pk'
    )}/verify"
    denial_link = f"{API_BASE_URL}/stores/{store_data.get('stores_pk')}/deny"

    user_id = store_data.get("users_fk")
    user_data = None
    if user_id:
        user_object = UserModel.find_user(user_id)
        if user_object:
            user_data = user_object.json()

    user_details_html = ""
    if user_data:
        user_details_html = f"""
            <tr>
                <td style="padding: 25px 30px; background-color: #2c585c;
                    border-radius: 8px; margin-bottom: 20px;">
                    <h2 style="margin-top: 0; margin-bottom: 15px; font-family:
                        'Helvetica Neue', Helvetica, Arial, sans-serif;
                            font-size: 20px; color: #FB8C00;">Owner Details
                    </h2>
                    <p style="margin: 4px 0; font-size: 16px; color: #ffffff;">
                        <strong>Name:</strong> {user_data.get(
                            "name", "Not provided"
                        )}
                    </p>
                    <p style="margin: 4px 0; font-size: 16px; color: #ffffff;">
                        <strong>User Name:</strong> {user_data.get(
                            "user_name", "Not provided"
                        )}
                    </p>
                    <p style="margin: 4px 0; font-size: 16px; color: #ffffff;">
                        <strong>Email:</strong> {user_data.get(
                            "email", "Not provided"
                        )}
                    </p>
                    <p style="margin: 4px 0; font-size: 16px; color: #ffffff;">
                        <strong>Join Date:</strong> {user_data.get(
                            "join_date", "Not provided"
                        )}
                    </p>
                </td>
            </tr>
        """
    else:
        user_details_html = f"""
            <tr>
                <td style="padding: 25px 30px; background-color: #2c585c; border-radius: 8px; margin-bottom: 20px;">
                    <h2 style="margin-top: 0; margin-bottom: 15px; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; font-size: 20px; color: #FB8C00;">Owner Details</h2>
                    <p style="margin: 4px 0; font-size: 16px; color: #ffffff;">Owner with ID {user_id} not found in the database.</p>
                </td>
            </tr>
        """

    store_details_html = f"""
        <tr>
            <td style="padding: 25px 30px; background-color: #2c585c; border-radius: 8px;">
                <h2 style="margin-top: 0; margin-bottom: 15px; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; font-size: 20px; color: #FB8C00;">Store Details</h2>
                <p style="margin: 4px 0; font-size: 16px; color: #ffffff;"><strong>Store ID:</strong> {store_data.get("stores_pk")}</p>
                <p style="margin: 4px 0; font-size: 16px; color: #ffffff;"><strong>Name:</strong> {store_data.get("name", "Not provided")}</p>
                <p style="margin: 4px 0; font-size: 16px; color: #ffffff;"><strong>Address:</strong> {store_data.get("address", "Not provided")}</p>
                <p style="margin: 4px 0; font-size: 16px; color: #ffffff;"><strong>Zip Code:</strong> {store_data.get("zip_code", "Not provided")}</p>
                <p style="margin: 4px 0; font-size: 16px; color: #ffffff;"><strong>State:</strong> {store_data.get("state", "Not provided")}</p>
                <p style="margin: 4px 0; font-size: 16px; color: #ffffff;"><strong>Website:</strong> <a href="{store_data.get("web_site", "#")}" style="color: #4CAF50;">{store_data.get("web_site", "Not provided")}</a></p>
                <p style="margin: 4px 0; font-size: 16px; color: #ffffff;"><strong>Picture Hash:</strong> {store_data.get("picture_hash", "Not provided")}</p>
            </td>
        </tr>
    """

    ses_client = boto3.client(
        "ses",
        region_name=str(AWS_REGION),
        aws_access_key_id=str(AWS_ACCESS_KEY_ID),
        aws_secret_access_key=str(AWS_SECRET_ACCESS_KEY),
    )

    mensagem = {
        "Subject": {"Data": subject},
        "Body": {
            "Html": {
                "Data": f"""
                    <!DOCTYPE html>
                    <html lang="en">
                    <head>
                        <meta charset="UTF-8">
                        <meta name="viewport" content="width=device-width, initial-scale=1.0">
                        <title>Store Verification</title>
                    </head>
                    <body style="margin: 0; padding: 0; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: #172A2C;">
                        <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #172A2C;">
                            <tr>
                                <td align="center" style="padding: 20px;">
                                    <table width="600" border="0" cellspacing="0" cellpadding="0" style="background-color: #274B4E; border-radius: 8px; color: #ffffff;">
                                        <tr>
                                            <td align="center" style="padding: 30px 20px;">
                                                <h1 style="margin: 0; color: #2196F3; font-size: 28px;">New Store Verification</h1>
                                                <p style="margin: 10px 0 0; font-size: 16px; color: #d0d0d0;">A new store has been registered and requires your approval.</p>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 0 30px;">
                                                <table width="100%" border="0" cellspacing="0" cellpadding="0">
                                                    {store_details_html}
                                                    <tr><td style="height: 20px;"></td></tr>
                                                    {user_details_html}
                                                </table>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td align="center" style="padding: 40px 20px;">
                                                <p style="margin-top: 0; margin-bottom: 25px; font-size: 16px; color: #d0d0d0;">Choose an action for this store:</p>
                                                <a href="{verification_link}" target="_blank" style="display: inline-block; padding: 15px 35px; color: #FFFFFF; background-color: #4CAF50; text-decoration: none; border-radius: 50px; font-weight: bold; font-size: 18px; letter-spacing: 0.5px; margin: 5px;">
                                                    Verify Store
                                                </a>
                                                <a href="{denial_link}" target="_blank" style="display: inline-block; padding: 15px 35px; color: #FFFFFF; background-color: #f44336; text-decoration: none; border-radius: 50px; font-weight: bold; font-size: 18px; letter-spacing: 0.5px; margin: 5px;">
                                                    Deny Store
                                                </a>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td align="center" style="padding: 20px; font-size: 12px; color: #777;">
                                                This is an automated notification from Drunagor System.
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                        </table>
                    </body>
                    </html>
                """
            }
        },
    }

    try:
        response = ses_client.send_email(
            Source=sender,
            Destination={"ToAddresses": [recipient]},
            Message=mensagem,
        )
        return response
    except ClientError as e:
        print(f"Error sending email: {e.response['Error']['Message']}")
        return None


def send_store_denial_email(store_data):
    user_id = store_data.get("users_fk")
    if not user_id:
        print(
            f"Error: User FK not found for store {store_data.get('stores_pk')}. Cannot send denial email."
        )
        return None

    user_object = UserModel.find_user(user_id)
    if not user_object:
        print(f"Error: User with ID {user_id} not found. Cannot send denial email.")
        return None

    recipient = user_object.email
    sender = "no-reply@drunagor.app"
    subject = f"An update on your store submission: {store_data.get('name')}"
    store_name = store_data.get("name")

    ses_client = boto3.client(
        "ses",
        region_name=str(AWS_REGION),
        aws_access_key_id=str(AWS_ACCESS_KEY_ID),
        aws_secret_access_key=str(AWS_SECRET_ACCESS_KEY),
    )

    mensagem = {
        "Subject": {"Data": subject},
        "Body": {
            "Html": {
                "Data": f"""
                    <!DOCTYPE html>
                    <html lang="en">
                    <head>
                        <meta charset="UTF-8">
                        <meta name="viewport" content="width=device-width, initial-scale=1.0">
                        <title>Store Submission Update</title>
                    </head>
                    <body style="font-family: Arial, sans-serif; background-color: #172A2C; color: #FFFFFF; padding: 20px; text-align: center;">
                        <div style="background-color: #274B4E; padding: 20px; border-radius: 8px; max-width: 500px; margin: 0 auto; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                            <h1 style="color: #f44336;">Store Submission Update</h1>
                            <p style="font-size: 16px; color: #d0d0d0;">Hello,</p>
                            <p style="font-size: 16px; color: #d0d0d0;">Thank you for submitting your store, '{store_name}', for review.</p>
                            <p style="font-size: 16px; color: #d0d0d0;">After careful consideration, we have decided not to approve the submission at this time. This can happen for a variety of reasons, including incomplete information or a mismatch with our platform's focus.</p>
                            <p style="margin-top: 20px; font-size: 14px; color: #B0BEC5;">If you have questions or would like more information, please contact james@wearecgs.com.</p>
                            <p style="margin-top: 30px; font-size: 12px; color: #777;">Thank you for your understanding.</p>
                        </div>
                    </body>
                    </html>
                """
            }
        },
    }

    try:
        response = ses_client.send_email(
            Source=sender,
            Destination={"ToAddresses": [recipient]},
            Message=mensagem,
        )
        return response
    except ClientError as e:
        print(f"Error sending denial email: {e.response['Error']['Message']}")
        return None


def reset_password(recipient, subject, password):
    sender = "no-reply@drunagor.app"

    ses_client = boto3.client(
        "ses",
        region_name=str(
            AWS_REGION
        ),  # Substitua 'sua_regiao' pela região desejada (ex: 'us-west-2')
        aws_access_key_id=str(
            AWS_ACCESS_KEY_ID
        ),  # Substitua 'sua_access_key_id' pela sua Access Key ID
        aws_secret_access_key=str(
            AWS_SECRET_ACCESS_KEY
        ),  # Substitua 'sua_secret_access_key' pela sua Secret Access Key
    )
    mensagem = {
        "Subject": {"Data": subject},  # Assunto do e-mail
        "Body": {
            "Html": {
                "Data": f"""
                        <html>
                            <head>
                                <meta charset="UTF-8">
                                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                                <title>Reset Password - Drunagor</title>
                            </head>
                            <body style="font-family: Arial, sans-serif; background-color: #172A2C; color: #FFFFFF; padding: 20px; text-align: center;">
                                <div style="background-color: #274B4E; padding: 20px; border-radius: 8px; max-width: 500px; margin: 0 auto; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                                    <h1 style="color: #2196F3;">Password Reset</h1>
                                    <p>Your password has been reset. Use the new password below to log in:</p>
                                    <div style="background-color: #3C7376; padding: 10px; border-radius: 5px; display: inline-block; font-size: 18px; font-weight: bold; margin: 20px 0;">{password}</div>
                                    <p>We strongly recommend changing your password after logging in.</p>
                                    <a href="https://drunagor.app/login" style="display: inline-block; padding: 10px 20px; color: #FFFFFF; background-color: #FB8C00; text-decoration: none; border-radius: 5px; font-weight: bold; margin-top: 20px;">Log In</a>
                                    <p style="margin-top: 20px; font-size: 14px; color: #B0BEC5;">If you did not request this change, please contact our support team immediately.</p>
                                </div>
                            </body>
                        </html>
                        """
            }
        },
    }

    try:
        response = ses_client.send_email(
            Source=sender,
            Destination={"ToAddresses": [recipient]},
            Message=mensagem,
        )

        return response

    except ClientError as e:
        return e
        print({"error": str(e)}, 500)


def level_up(recipient, subject):
    sender = "invite@drunagor.app"

    ses_client = boto3.client(
        "ses",
        region_name=str(
            AWS_REGION
        ),  # Substitua 'sua_regiao' pela região desejada (ex: 'us-west-2')
        aws_access_key_id=str(
            AWS_ACCESS_KEY_ID
        ),  # Substitua 'sua_access_key_id' pela sua Access Key ID
        aws_secret_access_key=str(
            AWS_SECRET_ACCESS_KEY
        ),  # Substitua 'sua_secret_access_key' pela sua Secret Access Key
    )
    mensagem = {
        "Subject": {"Data": subject},  # Assunto do e-mail
        "Body": {
            "Html": {
                "Data": f"""
                        <html>
                            <head>
                            <meta charset="UTF-8" />
                            <meta name="viewport" content="width=device-width, initial-scale=1.0" />
                            <title>Level Up Your Drunagor Experience with the Drunagor Companion App!</title>
                            </head>

                            <body style="
                                    font-family: Arial, sans-serif;
                                    background-color: #172a2c;
                                    color: #ffffff;
                                    padding: 10px;
                                    text-align: center;
                                ">
                            <div style="
                                    background-color: #274b4e;
                                    padding: 10px;
                                    border-radius: 8px;
                                    max-width: 800px;
                                    margin: 0 auto;
                                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                                    ">
                                <a href="https://drunagor.app/" target="_blank">
                                <img src="https://druna-assets.s3.us-east-2.amazonaws.com/landing-page/DrunagorAPP+Digital+Brochure+(1)-min.jpg"
                                    alt="Drunagor Library" style="max-width: 100%; height: auto; margin-bottom: 20px; border-radius: 8px;" />
                                </a>

                                <a href="https://drunagor.app/" target="_blank">
                                <img src="https://druna-assets.s3.us-east-2.amazonaws.com/landing-page/Frame+340.png" alt="Join Drunagor"
                                    style="max-width: 30%; height: auto; border-radius: 8px;" />
                                </a>
                            </div>
                            </body>

                        </html>
                        """
            }
        },
    }

    try:
        response = ses_client.send_email(
            Source=sender,
            Destination={"ToAddresses": [recipient]},
            Message=mensagem,
        )

        return response

    except ClientError as e:
        print({"error": str(e)}, 500)
