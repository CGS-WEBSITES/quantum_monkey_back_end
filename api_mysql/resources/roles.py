import traceback
from flask_restx import Resource, Namespace, reqparse, fields, marshal
from models.roles import RolesModel
from flask_jwt_extended import jwt_required
from sql_alchemy import MySQLConnection
from utils import boolean_string


role = Namespace("Roles", "Roles related Endpoints")


@role.route("/cadastro")
class RoleRegister(Resource):

    atributos = reqparse.RequestParser()
    atributos.add_argument(
        "name",
        type=str,
        required=True,
    ),
    atributos.add_argument("active", type=bool, required=False, default=True),

    @role.expect(atributos, validate=True)
    @jwt_required()
    def post(self):
        dados = self.atributos.parse_args()

        if RolesModel.find_by_name(dados["name"]):
            return (
                {"message": "The role '{}' already exists.".format(dados["name"])},
                400,
            )

        role = RolesModel(**dados)
        try:
            role.save_role()

        except:
            role.remove_role()
            traceback.print_exc()
            return {"message": "Internal server error"}, 500

        return {
            "message": "Role created successfully",
            "user": role.json(),
        }, 201  # Created


@role.route("/search")
class RoleSearch(Resource):
    role_model = role.model(
        "Roles Model",
        {
            "roles_pk": fields.Integer(required=True, description="Role key"),
            "name": fields.String(
                required=True, max_length=145, description="Role name"
            ),
            "active": fields.Boolean(
                required=True, description="Role is visible for users?"
            ),
        },
    )

    retorno_model = role.model(
        "Search role Model",
        {
            "roles": fields.List(fields.Nested(role_model)),
        },
    )

    parser = role.parser()
    parser.add_argument("name", type=str, required=False)
    parser.add_argument("active", type=boolean_string, required=False, default=True)

    @jwt_required()
    @role.expect(parser)
    @role.marshal_with(retorno_model)
    def get(self):
        CAMPOS = ["roles_pk", "name", "active"]
        dados = self.parser.parse_args()

        query = """SELECT roles_pk, name, active FROM roles """
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

        roles = []
        if resultado:
            for linha in resultado:
                aux_dict = {}
                for chave, valor in zip(CAMPOS, linha):
                    aux_dict[chave] = valor
                roles.append(aux_dict.copy())

        retorno = {
            "roles": roles,
        }

        return marshal(retorno, self.retorno_model), 200


@role.route("/<int:roles_pk>")
class RoleGet(Resource):

    @jwt_required()
    def get(self, roles_pk):
        role = RolesModel.find_role(roles_pk)

        if role:
            return role.json(), 200

        return {"message": "Role not found."}, 404  # not found


@role.route("/<int:roles_pk>/delete/")
class RoleDelete(Resource):

    @jwt_required()
    def delete(self, roles_pk):
        try:
            role = RolesModel.find_role(roles_pk)
            if role:
                role.delete_role()
                return {"message": "role successfully deleted"}, 200
            return {"message": "role not found."}, 404
        except:
            return {"message": "Internal server error"}, 500
