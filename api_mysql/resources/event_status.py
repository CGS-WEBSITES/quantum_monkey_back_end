import traceback
from flask_restx import Resource, Namespace, reqparse, fields, marshal
from models.event_status import EventStatusModel
from flask_jwt_extended import jwt_required
from sql_alchemy import MySQLConnection
from utils import boolean_string


status = Namespace("Envent Status", "Envent Status related Endpoints")


@status.route("/cadastro")
class RoleRegister(Resource):

    atributos = reqparse.RequestParser()
    atributos.add_argument(
        "name",
        type=str,
        required=True,
    ),
    atributos.add_argument("active", type=bool, required=False, default=True),

    @status.expect(atributos, validate=True)
    @jwt_required()
    def post(self):
        dados = self.atributos.parse_args()

        if EventStatusModel.find_by_name(dados["name"]):
            return (
                {"message": "The status '{}' already exists.".format(dados["name"])},
                400,
            )

        status = EventStatusModel(**dados)
        try:
            status.save_status()

        except:
            status.remove_status()
            traceback.print_exc()
            return {"message": "Internal server error"}, 500

        return {
            "message": "Role created successfully",
            "user": status.json(),
        }, 201  # Created


@status.route("/search")
class RoleSearch(Resource):
    status_model = status.model(
        "Envent Status Model",
        {
            "event_status_pk": fields.Integer(required=True, description="Role key"),
            "name": fields.String(
                required=True, max_length=145, description="Role name"
            ),
            "active": fields.Boolean(
                required=True, description="Role is visible for users?"
            ),
        },
    )

    retorno_model = status.model(
        "Search status Model",
        {
            "event_status": fields.List(fields.Nested(status_model)),
        },
    )

    parser = status.parser()
    parser.add_argument("name", type=str, required=False)
    parser.add_argument("active", type=boolean_string, required=False, default=True)

    @jwt_required()
    @status.expect(parser)
    @status.marshal_with(retorno_model)
    def get(self):
        CAMPOS = ["event_status_pk", "name", "active"]
        dados = self.parser.parse_args()

        query = """SELECT event_status_pk, name, active FROM event_status """
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

        event_status = []
        if resultado:
            for linha in resultado:
                aux_dict = {}
                for chave, valor in zip(CAMPOS, linha):
                    aux_dict[chave] = valor
                event_status.append(aux_dict.copy())

        retorno = {
            "event_status": event_status,
        }

        return marshal(retorno, self.retorno_model), 200


@status.route("/<int:event_status_pk>")
class RoleGet(Resource):

    @jwt_required()
    def get(self, event_status_pk):
        status = EventStatusModel.find_status(event_status_pk)

        if status:
            return status.json(), 200

        return {"message": "Role not found."}, 404  # not found


@status.route("/<int:event_status_pk>/delete/")
class RoleDelete(Resource):

    @jwt_required()
    def delete(self, event_status_pk):
        try:
            status = EventStatusModel.find_status(event_status_pk)
            if status:
                status.delete_status()
                return {"message": "status successfully deleted"}, 200
            return {"message": "status not found."}, 404
        except:
            return {"message": "Internal server error"}, 500
