import traceback
from flask_restx import Resource, Namespace, reqparse, fields, marshal
from models.sceneries import SceneriesModel
from flask_jwt_extended import jwt_required
from sql_alchemy import MySQLConnection
from utils import boolean_string


scenery = Namespace("Sceneries", "Sceneries related Endpoints")


@scenery.route("/cadastro")
class SceneryRegister(Resource):

    atributos = reqparse.RequestParser()
    atributos.add_argument(
        "name",
        type=str,
        required=True,
    ),
    atributos.add_argument(
        "sceneries_hash",
        type=str,
        required=True,
    ),
    atributos.add_argument("active", type=bool, required=False, default=True),

    @scenery.expect(atributos, validate=True)
    @jwt_required()
    def post(self):
        dados = self.atributos.parse_args()

        if SceneriesModel.find_by_name(dados["name"]):
            return (
                {"message": "The scenery '{}' already exists.".format(dados["name"])},
                400,
            )

        scenery = SceneriesModel(**dados)

        try:
            scenery.save()

        except:
            scenery.remove()
            return {"message": "Internal server error"}, 500

        return {
            "message": "Scenery created successfully",
            "user": scenery.json(),
        }, 201  # Created


@scenery.route("/search")
class ScenerySearch(Resource):
    scenery_model = scenery.model(
        "Scenery Model",
        {
            "sceneries_pk": fields.Integer(required=True, description="Scenery key"),
            "name": fields.String(
                required=True, max_length=145, description="Scenery name"
            ),
            "sceneries_hash": fields.String(
                required=True, max_length=145, description="Scenery Hash"
            ),
            "active": fields.Boolean(
                required=True, description="Scenery is visible for users?"
            ),
        },
    )

    retorno_model = scenery.model(
        "Search scenery Model",
        {
            "sceneries": fields.List(fields.Nested(scenery_model)),
        },
    )

    parser = scenery.parser()
    parser.add_argument("name", type=str, required=False)
    parser.add_argument("active", type=boolean_string, required=False, default=True)

    @jwt_required()
    @scenery.expect(parser)
    @scenery.marshal_with(retorno_model)
    def get(self):
        CAMPOS = ["sceneries_pk", "name", "sceneries_hash", "active"]
        dados = self.parser.parse_args()

        query = """SELECT sceneries_pk, name, sceneries_hash, active FROM sceneries """
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

        sceneries = []
        if resultado:
            for linha in resultado:
                aux_dict = {}
                for chave, valor in zip(CAMPOS, linha):
                    aux_dict[chave] = valor
                sceneries.append(aux_dict.copy())

        retorno = {
            "sceneries": sceneries,
        }

        return marshal(retorno, self.retorno_model), 200


@scenery.route("/<int:sceneries_pk>")
class SceneryGet(Resource):

    @jwt_required()
    def get(self, sceneries_pk):
        scenery = SceneriesModel.find_scenery(sceneries_pk)

        if scenery:
            return scenery.json(), 200

        return {"message": "Scenery not found."}, 404  # not found


@scenery.route("/<int:sceneries_pk>/delete/")
class SceneryDelete(Resource):

    @jwt_required()
    def delete(self, sceneries_pk):
        try:
            scenery = SceneriesModel.find_scenery(sceneries_pk)
            if scenery:
                scenery.delete()
                return {"message": "scenery successfully deleted"}, 200
            return {"message": "scenery not found."}, 404
        except:
            return {"message": "Internal server error"}, 500
