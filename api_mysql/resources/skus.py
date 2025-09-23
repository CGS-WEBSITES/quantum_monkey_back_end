import traceback
from flask_restx import Resource, Namespace, reqparse, fields, marshal
from models.skus import SkusModel
from flask_jwt_extended import jwt_required
from sql_alchemy import MySQLConnection
from math import ceil
from utils import boolean_string


sku = Namespace("Skus", "skus related Endpoints")


@sku.route("/cadastro")
class SkuRegister(Resource):

    atributos = reqparse.RequestParser()
    atributos.add_argument(
        "name",
        type=str,
        required=True,
    ),
    atributos.add_argument(
        "link",
        type=str,
        required=True,
    ),
    atributos.add_argument(
        "color",
        type=str,
        required=True,
    ),
    atributos.add_argument(
        "background",
        type=str,
        required=True,
    ),
    atributos.add_argument(
        "picture_hash",
        type=str,
        required=True,
    ),
    atributos.add_argument("active", type=bool, required=False, default=True),

    @sku.expect(atributos, validate=True)
    @jwt_required()
    def post(self):
        dados = self.atributos.parse_args()

        if SkusModel.find_by_name(dados["name"]):
            return (
                {"message": "The sku '{}' already exists.".format(dados["name"])},
                400,
            )

        sku = SkusModel(**dados)
        try:
            sku.save_sku()

        except:
            sku.remove_sku()
            traceback.print_exc()
            return {"message": "Internal server error"}, 500

        return {
            "message": "sku created successfully",
            "user": sku.json(),
        }, 201  # Created


@sku.route("/search")
class SkuSearch(Resource):
    sku_model = sku.model(
        "Skus Model",
        {
            "skus_pk": fields.Integer(required=True, description="sku key"),
            "libraries_pk": fields.Integer(required=True, description="sku key"),
            "name": fields.String(
                required=True, max_length=145, description="sku name"
            ),
            "link": fields.String(
                required=True, max_length=200, description="sku name"
            ),
            "color": fields.String(
                required=True, max_length=200, description="sku name"
            ),
            "background": fields.String(
                required=True, max_length=200, description="sku name"
            ),
            "picture_hash": fields.String(
                required=True, max_length=200, description="sku name"
            ),
            "wish": fields.Boolean(
                required=True, description="sku is visible for users?"
            ),
            "owned": fields.Boolean(
                required=True, description="sku is visible for users?"
            ),
        },
    )

    retorno_model = sku.model(
        "Search sku Model",
        {
            "skus": fields.List(fields.Nested(sku_model)),
            "current_page": fields.Integer,
            "last_page": fields.Integer,
        },
    )

    parser = sku.parser()
    parser.add_argument("users_fk", type=int, required=True)
    parser.add_argument("active", type=boolean_string, required=False, default=True)
    parser.add_argument("limit", type=int, required=False, default=30)
    parser.add_argument("offset", type=int, required=False, default=0)

    @jwt_required()
    @sku.expect(parser)
    @sku.marshal_with(retorno_model)
    def get(self):
        CAMPOS = [
            "skus_pk",
            "libraries_pk",
            "name",
            "link",
            "color",
            "background",
            "picture_hash",
            "wish",
            "owned",
        ]

        dados = self.parser.parse_args()

        query = """SELECT
	                    S.skus_pk,
                        L.libraries_pk,
                        S.name,
                        S.link,
                        S.color,
                        S.background,
                        S.picture_hash,
                        L.wish,
                        L.owned
                    FROM
                        skus S
                    LEFT JOIN (
                        SELECT
                            *
                        from
                            libraries L
                        WHERE
                            L.active = TRUE
                                and """

        query_params = []

        query += "L.users_fk = %s "
        query_params.append(dados["users_fk"])

        query += """) L ON S.skus_pk = L.skus_fk 
                    WHERE S.active = %s"""

        query_params.append(dados["active"])

        conn = MySQLConnection()
        resultado = conn.execute(query, tuple(query_params))

        contagem = "SELECT COUNT(*) FROM (" + query + ") as users_contagem;"
        ocorrencias = conn.execute(contagem, tuple(query_params))[0][0]
        pagina_atual = int(dados["offset"] / dados["limit"]) + 1
        ultima_pagina = ceil(ocorrencias / dados["limit"])

        skus = []
        if resultado:
            for linha in resultado:
                aux_dict = {}
                for chave, valor in zip(CAMPOS, linha):
                    aux_dict[chave] = valor
                skus.append(aux_dict.copy())

        else:
            return {"message": "None country found with the required filters."}, 404

        retorno = {
            "skus": skus,
            "current_page": pagina_atual,
            "last_page": ultima_pagina,
        }

        return marshal(retorno, self.retorno_model), 200


@sku.route("/<int:skus_pk>")
class skuGet(Resource):

    @jwt_required()
    def get(self, skus_pk):
        sku = SkusModel.find_sku(skus_pk)

        if sku:
            return sku.json(), 200

        return {"message": "sku not found."}, 404  # not found


@sku.route("/<int:skus_pk>/delete/")
class skuDelete(Resource):

    @jwt_required()
    def delete(self, skus_pk):
        try:
            sku = SkusModel.find_sku(skus_pk)
            if sku:
                sku.delete_sku()
                return {"message": "sku successfully deleted"}, 200
            return {"message": "sku not found."}, 404
        except:
            return {"message": "Internal server error"}, 500
