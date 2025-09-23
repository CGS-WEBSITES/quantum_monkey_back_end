import traceback
from flask_restx import Resource, Namespace, reqparse, fields, marshal
from models.seasons import SeasonsModel
from flask_jwt_extended import jwt_required
from sql_alchemy import MySQLConnection
from utils import boolean_string


season = Namespace("Seasons", "Seasons related Endpoints")


@season.route("/cadastro")
class SeasonRegister(Resource):

    atributos = reqparse.RequestParser()
    atributos.add_argument(
        "name",
        type=str,
        required=True,
    ),
    atributos.add_argument(
        "season_hash",
        type=str,
        required=True,
    ),
    atributos.add_argument("active", type=bool, required=False, default=True),

    @season.expect(atributos, validate=True)
    @jwt_required()
    def post(self):
        dados = self.atributos.parse_args()

        if SeasonsModel.find_by_name(dados["name"]):
            return (
                {"message": "The season '{}' already exists.".format(dados["name"])},
                400,
            )

        season = SeasonsModel(**dados)

        try:
            season.save()

        except:
            season.remove()
            return {"message": "Internal server error"}, 500

        return {
            "message": "Season created successfully",
            "user": season.json(),
        }, 201  # Created


@season.route("/search")
class SeasonSearch(Resource):
    season_model = season.model(
        "Season Model",
        {
            "seasons_pk": fields.Integer(required=True, description="Season key"),
            "name": fields.String(
                required=True, max_length=145, description="Season name"
            ),
            "season_hash": fields.String(
                required=True, max_length=145, description="Season Hash"
            ),
            "active": fields.Boolean(
                required=True, description="Season is visible for users?"
            ),
        },
    )

    retorno_model = season.model(
        "Search season Model",
        {
            "seasons": fields.List(fields.Nested(season_model)),
        },
    )

    parser = season.parser()
    parser.add_argument("name", type=str, required=False)
    parser.add_argument("active", type=boolean_string, required=False, default=True)

    @jwt_required()
    @season.expect(parser)
    @season.marshal_with(retorno_model)
    def get(self):
        CAMPOS = ["seasons_pk", "name", "season_hash", "active"]
        dados = self.parser.parse_args()

        query = """SELECT seasons_pk, name, season_hash, active FROM seasons """
        query_params = []

        if dados["name"]:
            query += "WHERE name LIKE %s "
            query_params.append("%" + dados["name"] + "%")
            where = True
        else:
            where = False

        if where:
            query += "AND active = %s;"
        else:
            query += "WHERE active = %s;"

        query_params.append(dados["active"])

        conn = MySQLConnection()
        resultado = conn.execute(query, tuple(query_params))

        seasons = []
        if resultado:
            for linha in resultado:
                aux_dict = {}
                for chave, valor in zip(CAMPOS, linha):
                    aux_dict[chave] = valor
                seasons.append(aux_dict.copy())

        retorno = {
            "seasons": seasons,
        }

        return marshal(retorno, self.retorno_model), 200


@season.route("/<int:seasons_pk>")
class SeasonGet(Resource):

    @jwt_required()
    def get(self, seasons_pk):
        season = SeasonsModel.find_season(seasons_pk)

        if season:
            return season.json(), 200

        return {"message": "Season not found."}, 404  # not found


@season.route("/<int:seasons_pk>/delete/")
class SeasonDelete(Resource):

    @jwt_required()
    def delete(self, seasons_pk):
        try:
            season = SeasonsModel.find_season(seasons_pk)
            if season:
                season.delete()
                return {"message": "season successfully deleted"}, 200
            return {"message": "season not found."}, 404
        except:
            return {"message": "Internal server error"}, 500
