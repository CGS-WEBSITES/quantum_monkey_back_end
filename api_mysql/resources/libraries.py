import traceback
from flask_restx import Resource, Namespace, reqparse, fields, marshal
from models.libraries import libraryModel
from flask_jwt_extended import jwt_required
from sql_alchemy import MySQLConnection
from datetime import datetime
from pytz import timezone
from utils import boolean_string


libraries = Namespace("Libary", "Libary related Endpoints")


@libraries.route("/cadastro")
class libraryRegister(Resource):

    atributos = reqparse.RequestParser()
    atributos.add_argument(
        "users_fk",
        type=int,
        required=True,
    )
    atributos.add_argument(
        "skus_fk",
        type=int,
        required=True,
    )
    atributos.add_argument("wish", type=boolean_string, required=True),
    atributos.add_argument("owned", type=boolean_string, required=True),
    atributos.add_argument(
        "number",
        type=int,
        required=False,
    )
    atributos.add_argument("active", type=bool, required=False, default=True),

    @libraries.expect(atributos, validate=True)
    @jwt_required()
    def post(self):
        dados = self.atributos.parse_args()

        if dados["wish"] == dados["owned"]:
            return {
                "message": "A SKU can't be owned and on the wish list at the same time",
            }, 400

        library = libraryModel(**dados)
        try:
            library.save()

        except:
            library.remove()
            traceback.print_exc()
            return {"message": "Internal server error"}, 500

        return {
            "message": "rl_librarys_users created successfully",
            "rl_librarys_users": library.json(),
        }, 201  # Created


@libraries.route("/alter")
class libraryAlter(Resource):

    atributos = reqparse.RequestParser()
    atributos.add_argument(
        "libraries_pk",
        type=int,
        required=True,
    ),
    atributos.add_argument(
        "users_fk",
        type=int,
        required=True,
    )
    atributos.add_argument(
        "skus_fk",
        type=int,
        required=True,
    )
    atributos.add_argument("wish", type=boolean_string, required=False),
    atributos.add_argument("owned", type=boolean_string, required=False),
    atributos.add_argument(
        "number",
        type=int,
        required=False,
    )

    @jwt_required()
    @libraries.expect(atributos, validate=True)
    def put(self):

        kwargs = self.atributos.parse_args()

        library = libraryModel.find_library(kwargs["libraries_pk"])

        if library:

            if (kwargs["wish"] == kwargs["owned"]) and kwargs["wish"] != False:
                return {
                    "message": "A SKU can't be owned and on the wish list at the same time",
                }, 400

            try:
                library.update(**kwargs)

                return {
                    "message": "library has been altered successfully.",
                    "data": library.json(),
                }, 200

            except:
                traceback.print_exc()
                return {"message": "Internal server error"}, 500

        return {"message": "library not found."}, 404


@libraries.route("/<int:library_pk>")
class libraryGet(Resource):

    @jwt_required()
    def get(self, library_pk):
        library = libraryModel.find_library(library_pk)

        if library:
            return library.json(), 200

        return {"message": "library not found."}, 404  # not found


@libraries.route("/<int:library_pk>/delete/")
class libraryDelete(Resource):

    @jwt_required()
    def delete(self, library_pk):
        try:
            library = libraryModel.find_library(library_pk)
            if library:
                library.delete()
                return {"message": "library successfully deleted"}, 200
            return {"message": "library not found."}, 404
        except:
            return {"message": "Internal server error"}, 500
