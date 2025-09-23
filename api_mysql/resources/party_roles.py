import traceback
from flask_restx import Resource, Namespace, reqparse, fields, marshal
from models.party_roles import partyRolesModel
from flask_jwt_extended import jwt_required
from sql_alchemy import MySQLConnection
from utils import boolean_string


party_role = Namespace("Party Roles", "Party roles related Endpoints")


@party_role.route("/cadastro")
class party_roleRegister(Resource):

    atributos = reqparse.RequestParser()
    atributos.add_argument(
        "name",
        type=str,
        required=True,
    ),
    atributos.add_argument("active", type=bool, required=False, default=True),

    @party_role.expect(atributos, validate=True)
    @jwt_required()
    def post(self):
        dados = self.atributos.parse_args()

        if partyRolesModel.find_by_name(dados["name"]):
            return (
                {
                    "message": "The party_role '{}' already exists.".format(
                        dados["name"]
                    )
                },
                400,
            )

        party_role = partyRolesModel(**dados)
        try:
            party_role.save_party_role()

        except:
            party_role.remove_party_role()
            traceback.print_exc()
            return {"message": "Internal server error"}, 500

        return {
            "message": "party_role created successfully",
            "user": party_role.json(),
        }, 201  # Created


@party_role.route("/search")
class party_roleSearch(Resource):
    party_role_model = party_role.model(
        "party_roles Model",
        {
            "party_roles_pk": fields.Integer(
                required=True, description="party_role key"
            ),
            "name": fields.String(
                required=True, max_length=145, description="party_role name"
            ),
            "active": fields.Boolean(
                required=True, description="party_role is visible for users?"
            ),
        },
    )

    retorno_model = party_role.model(
        "Search party_role Model",
        {
            "party_roles": fields.List(fields.Nested(party_role_model)),
        },
    )

    parser = party_role.parser()
    parser.add_argument("name", type=str, required=False)
    parser.add_argument("active", type=boolean_string, required=False, default=True)

    @jwt_required()
    @party_role.expect(parser)
    @party_role.marshal_with(retorno_model)
    def get(self):
        CAMPOS = ["party_roles_pk", "name", "active"]
        dados = self.parser.parse_args()

        query = """SELECT party_roles_pk, name, active FROM party_roles """
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

        party_roles = []
        if resultado:
            for linha in resultado:
                aux_dict = {}
                for chave, valor in zip(CAMPOS, linha):
                    aux_dict[chave] = valor
                party_roles.append(aux_dict.copy())

        retorno = {
            "party_roles": party_roles,
        }

        return marshal(retorno, self.retorno_model), 200


@party_role.route("/<int:party_roles_pk>")
class party_roleGet(Resource):

    @jwt_required()
    def get(self, party_roles_pk):
        party_role = partyRolesModel.find_party_role(party_roles_pk)

        if party_role:
            return party_role.json(), 200

        return {"message": "party_role not found."}, 404  # not found


@party_role.route("/<int:party_roles_pk>/delete/")
class party_roleDelete(Resource):

    @jwt_required()
    def delete(self, party_roles_pk):
        try:
            party_role = partyRolesModel.find_party_role(party_roles_pk)
            if party_role:
                party_role.delete_party_role()
                return {"message": "party_role successfully deleted"}, 200
            return {"message": "party_role not found."}, 404
        except:
            return {"message": "Internal server error"}, 500
