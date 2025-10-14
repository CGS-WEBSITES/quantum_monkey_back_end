import traceback
from datetime import datetime
from flask_restx import Resource, Namespace, reqparse, fields, marshal
from models.users import UserModel
from flask_jwt_extended import (
    create_access_token,
    get_jwt,
    jwt_required,
)
from bcryptInit import bcrypt
from blacklist import BLACKLIST
from sql_alchemy import MySQLConnection
from math import ceil
import hashlib
from utils import random_password
from datetime import datetime
from pytz import timezone
from email_sender import reset_password


user = Namespace("Users", "User related Endpoints")


@user.route("/cadastro")
class UserRegister(Resource):

    atributos = reqparse.RequestParser()
    atributos.add_argument(
        "name",
        type=str,
        required=True,
    ),
    atributos.add_argument(
        "email",
        type=str,
        required=True,
    ),
    atributos.add_argument(
        "password",
        type=str,
        required=True,
    ),
    atributos.add_argument("active", type=bool, required=False, default=True),

    @user.expect(atributos, validate=True)
    def post(self):
        dados = self.atributos.parse_args()

        user = UserModel(**dados)

        try:
            user.save_user()

        except:
            user.delete_user()
            traceback.print_exc()
            return {"message": "Internal server error"}, 500

        return {
            "message": "User successfully created!",
            "user": user.json(),
        }, 201  # Created


@user.route("/login")
class UserLogin(Resource):

    atributos = reqparse.RequestParser()
    atributos.add_argument(
        "login",
        type=str,
        required=True,
    )
    atributos.add_argument(
        "password",
        type=str,
        required=True,
    )

    @classmethod
    @user.expect(atributos, validate=True)
    def post(cls):
        dados = cls.atributos.parse_args()
        user = UserModel.find_by_email(dados["login"])

        # try:
        if user and bcrypt.check_password_hash(user.password, dados["password"]):
            access_token = create_access_token(identity=user.users_pk)

            if not user.active:
                return {"message": "Not Authorized."}, 403

            else:
                return {
                    "message": "User successfully logged in.",
                    "data": user.json(),
                    "access_token": access_token,
                }, 200

        return {"message": "Incorrect password or login"}, 403

        # except:
        #     return {"message": "Internal server error."}, 500


@user.route("/logout")
class UserLogout(Resource):
    @jwt_required()
    def post(self):
        jwt_id = get_jwt()["jti"]  # JWT Token Identifier
        BLACKLIST.add(jwt_id)
        try:
            return {"message": "Logged out successfuly!"}, 200
        except:
            return {"message": "Um erro interno ocorreu"}, 500


@user.route("/alter")
class UserAlter(Resource):

    atributos = reqparse.RequestParser()
    atributos.add_argument(
        "name",
        type=str,
        required=False,
    ),
    atributos.add_argument(
        "email",
        type=str,
        required=False,
    ),

    @jwt_required()
    @user.expect(atributos, validate=True)
    def put(self):
        kwargs = self.atributos.parse_args()

        if kwargs["email"]:
            user = UserModel.find_by_email(kwargs["email"])
            if user:
                {"message": "Email already registered."}, 401

        user = UserModel.find_user(kwargs["users_pk"])

        if kwargs["password"]:
            hash_md5 = hashlib.md5()
            hash_md5.update(kwargs["password"].encode("utf-8"))

            kwargs["password"] = hash_md5.hexdigest()
            kwargs["password"] = bcrypt.generate_password_hash(
                kwargs["password"]
            ).decode("UTF-8")

        if user:

            try:
                user.update_user(**kwargs)

                return {
                    "message": "User has been altered successfully.",
                    "data": user.json(),
                }, 200

            except:
                traceback.print_exc()
                return {"message": "Internal server error"}, 500

        return {"message": "User not found."}, 404


@user.route("/<int:users_pk>")
class UserGet(Resource):

    @jwt_required()
    def get(self, users_pk):
        user = UserModel.find_user(users_pk)

        if user:
            return user.json(), 200

        return {"message": "Usuário não encontrado."}, 404  # not found


@user.route("/<int:users_pk>/delete/")
class UserDelete(Resource):

    @jwt_required()
    def delete(self, users_pk):
        # try:
        user = UserModel.find_user(users_pk)
        if user:
            user.delete_user()
            return {"message": "User successfully deleted"}, 200
        return {"message": "User not found."}, 404

        # except:
        #     return {"message": "Internal server error"}, 500


@user.route("/<int:users_pk>/change_email/")
class UserChangeEmail(Resource):
    atributos = reqparse.RequestParser()
    atributos.add_argument(
        "email",
        type=str,
        required=True,
    ),

    @jwt_required()
    @user.expect(atributos, validate=True)
    def put(self, users_pk):
        user = UserModel.find_user(users_pk)
        if user:
            kwargs = self.atributos.parse_args()
            try:
                user.update_user(**kwargs)

                return user.json(), 200

            except:
                traceback.print_exc()
                return {"message": "Internal server error"}, 500

        return {"message": "User not found."}, 404


@user.route("/alter_password")
class ChagePassword(Resource):
    atributos = user.parser()
    atributos.add_argument(
        "email",
        type=str,
        required=True,
        help="User email",
    )
    atributos.add_argument(
        "password",
        type=str,
        required=True,
        help="New password",
    )

    @jwt_required()
    @user.expect(atributos)
    def post(self):
        dados = self.atributos.parse_args()
        user = UserModel.find_by_email(dados.email)
        if not user:
            return {"message": "User with email {} not found.".format(dados.email)}, 404

        try:
            user.update_user(dados)
            return (
                {
                    "message": "Password altered successfully",
                },
                200,
            )
        except:
            return (
                {"message": "Internal server error."},
                500,
            )


@user.route("/reset_password")
class ChagePasswordRequisition(Resource):
    atributos = user.parser()
    atributos.add_argument(
        "email",
        type=str,
        required=True,
        help="The email field cannot be left blank",
    )

    @classmethod
    @user.expect(atributos)
    @user.doc(responses={200: "E-mail sent successfully."})
    @user.doc(responses={404: "User not found."})
    @user.doc(responses={500: "Internal server error."})
    def post(cls):
        dados = cls.atributos.parse_args()
        user = UserModel.find_by_email(dados.email)
        # password = random_password()
        password = "12345"

        hash_md5 = hashlib.md5()
        hash_md5.update(password.encode("utf-8"))

        enc_pswd = hash_md5.hexdigest()
        enc_pswd = bcrypt.generate_password_hash(enc_pswd).decode("UTF-8")

        if not user:
            return {
                "message": "User with mail {} was not found.".format(dados.email)
            }, 404

        try:
            response = reset_password(
                dados.email, "Your Drunagor Account Password Has Been Reset", password
            )

            if response["ResponseMetadata"]["HTTPStatusCode"] == 200:

                try:
                    user.set_password(enc_pswd)

                except:
                    return (
                        {"message": "Internal server error while saving user"},
                        500,
                    )

        except:
            return (
                {"message": "Internal server error while sending email"},
                500,
            )

        return (
            {
                "message": "The e-mail was sent successfully.",
                "response": response,
            },
            200,
        )
