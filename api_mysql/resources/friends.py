import traceback
from flask_restx import Resource, Namespace, reqparse, fields, marshal
from models.friends import friendModel
from flask_jwt_extended import jwt_required
from sql_alchemy import MySQLConnection
from utils import boolean_string
from math import ceil


friends = Namespace("Friends", "Friend related Endpoints")


@friends.route("/register")
class friendRegister(Resource):

    atributos = reqparse.RequestParser()

    atributos.add_argument(
        "invite_users_fk",
        type=int,
        required=True,
    )

    atributos.add_argument(
        "recipient_users_fk",
        type=int,
        required=True,
    )

    atributos.add_argument(
        "active", type=boolean_string, required=False, default="true"
    ),

    @friends.expect(atributos, validate=True)
    @jwt_required()
    def post(self):
        dados = self.atributos.parse_args()

        dados["accepted"] = False

        friend = friendModel(**dados)

        old_friend = friend.find_friend(
            dados["invite_users_fk"], dados["recipient_users_fk"]
        )

        if old_friend:
            return {
                "message": "Already requested",
            }, 400

        try:
            friend.save()

        except:
            friend.remove()
            traceback.print_exc()
            return {"message": "Internal server error"}, 500

        return {
            "message": "rl_friends_users created successfully",
            "rl_friends_users": friend.json(),
        }, 201  # Created


@friends.route("/alter")
class friendAlter(Resource):

    atributos = reqparse.RequestParser()

    atributos.add_argument(
        "friends_pk",
        type=int,
        required=True,
    )

    atributos.add_argument(
        "recipient_users_fk",
        type=int,
        required=True,
    )

    atributos.add_argument(
        "accepeted", type=boolean_string, required=False, default="true"
    )

    @jwt_required()
    @friends.expect(atributos, validate=True)
    def put(self):

        kwargs = self.atributos.parse_args()

        friend = friendModel.find_by_pk(kwargs["friends_pk"])

        if friend:
            try:
                friend.update(**kwargs)

                return {
                    "message": "friendship has been altered successfully.",
                    "data": friend.json(),
                }, 200

            except:
                traceback.print_exc()
                return {"message": "Internal server error"}, 500

        return {"message": "friendship not found."}, 404


@friends.route("/accept/<int:friends_pk>")
class friendAlter(Resource):

    @jwt_required()
    def put(self, friends_pk):

        friend = friendModel.find_by_pk(friends_pk)

        if friend:
            try:
                friend.accept()

                return {
                    "message": "friendship accepted successfully.",
                    "data": friend.json(),
                }, 200

            except:
                traceback.print_exc()
                return {"message": "Internal server error"}, 500

        return {"message": "friendship not found."}, 404


@friends.route("/list_friends")
class friendList(Resource):

    friend_model = friends.model(
        "Friends Model",
        {
            "friends_pk": fields.Integer(required=True, description="Relationship key"),
            "invite_users_fk": fields.Integer(required=True, description="Invitor key"),
            "accepted": fields.Boolean(
                required=True, description="Is this relation accepted"
            ),
            "recipient_users_fk": fields.Integer(
                required=True, description="Recipient key"
            ),
            "user_name": fields.String(
                required=True, max_length=45, description="Nickname"
            ),
            "picture_hash": fields.String(
                required=False, max_length=200, description="Figure id in data lake"
            ),
            "join_date": fields.Date(required=True),
            "background_hash": fields.String(
                required=False, max_length=200, description="Figure id in data lake"
            ),
            "roles_fk": fields.Integer(
                required=True, description="User role in the system"
            ),
        },
    )

    retorno_model = friends.model(
        "Search sku Model",
        {
            "friends": fields.List(fields.Nested(friend_model)),
            "current_page": fields.Integer,
            "last_page": fields.Integer,
        },
    )

    parser = friends.parser()
    parser.add_argument("invite_users_fk", type=int, required=True)
    parser.add_argument("accepted", type=boolean_string, required=False, default=True)
    parser.add_argument("active", type=boolean_string, required=False, default=True)
    parser.add_argument("limit", type=int, required=False, default=30)
    parser.add_argument("offset", type=int, required=False, default=0)

    @jwt_required()
    @friends.expect(parser)
    @friends.marshal_with(retorno_model)
    def get(self):
        CAMPOS = [
            "friends_pk",
            "invite_users_fk",
            "accepted",
            "recipient_users_fk",
            "user_name",
            "picture_hash",
            "join_date",
            "background_hash",
            "roles_fk",
        ]

        dados = self.parser.parse_args()

        query = """SELECT
                        F.friends_pk,
                        F.invite_users_fk,
                        F.accepted,
                        F.recipient_users_fk,
                        U.user_name,
                        U.picture_hash,
                        U.join_date,
                        U.background_hash,
                        U.roles_fk
                    FROM
                        friends F
                    LEFT JOIN users U 
                        ON U.users_pk = CASE 
                            WHEN F.recipient_users_fk = %s THEN F.invite_users_fk
                            ELSE F.recipient_users_fk
                        END 
                    WHERE 
                        (F.invite_users_fk = %s OR F.recipient_users_fk = %s)
                        AND F.active = %s
                        AND F.accepted = %s """

        query_params = []

        query_params.append(dados["invite_users_fk"])

        query_params.append(dados["invite_users_fk"])

        query_params.append(dados["invite_users_fk"])

        query_params.append(dados["active"])

        query_params.append(dados["accepted"])

        conn = MySQLConnection()

        resultado = conn.execute(query, tuple(query_params))

        # return resultado

        contagem = "SELECT COUNT(*) FROM (" + query + ") as users_contagem;"
        ocorrencias = conn.execute(contagem, tuple(query_params))[0][0]
        pagina_atual = int(dados["offset"] / dados["limit"]) + 1
        ultima_pagina = ceil(ocorrencias / dados["limit"])

        friends = []
        if resultado:
            for linha in resultado:
                aux_dict = {}
                for chave, valor in zip(CAMPOS, linha):
                    aux_dict[chave] = valor
                friends.append(aux_dict.copy())

        else:
            return {"message": "None country found with the required filters."}, 404

        retorno = {
            "friends": friends,
            "current_page": pagina_atual,
            "last_page": ultima_pagina,
        }

        return marshal(retorno, self.retorno_model), 200


@friends.route("/list_requests")
class requestsList(Resource):

    requests_model = friends.model(
        "Requests Model",
        {
            "friends_pk": fields.Integer(required=True, description="Relationship key"),
            "invite_users_fk": fields.Integer(required=True, description="Invitor key"),
            "accepted": fields.Boolean(
                required=True, description="Is this relation accepted"
            ),
            "recipient_users_fk": fields.Integer(
                required=True, description="Recipient key"
            ),
            "user_name": fields.String(
                required=True, max_length=45, description="Nickname"
            ),
            "picture_hash": fields.String(
                required=False, max_length=200, description="Figure id in data lake"
            ),
            "join_date": fields.Date(required=True),
            "background_hash": fields.String(
                required=False, max_length=200, description="Figure id in data lake"
            ),
            "roles_fk": fields.Integer(
                required=True, description="User role in the system"
            ),
        },
    )

    retorno_model = friends.model(
        "Search sku Model",
        {
            "friends": fields.List(fields.Nested(requests_model)),
            "current_page": fields.Integer,
            "last_page": fields.Integer,
        },
    )

    parser = friends.parser()
    parser.add_argument("recipient_users_fk", type=int, required=True)
    parser.add_argument("accepted", type=boolean_string, required=False, default=True)
    parser.add_argument("active", type=boolean_string, required=False, default=True)
    parser.add_argument("limit", type=int, required=False, default=30)
    parser.add_argument("offset", type=int, required=False, default=0)

    @jwt_required()
    @friends.expect(parser)
    @friends.marshal_with(retorno_model)
    def get(self):
        CAMPOS = [
            "friends_pk",
            "invite_users_fk",
            "accepted",
            "recipient_users_fk",
            "user_name",
            "picture_hash",
            "join_date",
            "background_hash",
            "roles_fk",
        ]

        dados = self.parser.parse_args()

        query = """SELECT
                        F.friends_pk,
                        F.invite_users_fk,
                        F.accepted,
                        F.recipient_users_fk,
                        U.user_name,
                        U.picture_hash,
                        U.join_date,
                        U.background_hash,
                        U.roles_fk
                    FROM
                        friends F
                    LEFT JOIN users U ON
                        F.invite_users_fk = U.users_pk """

        query_params = []

        query += """WHERE
                        F.recipient_users_fk = %s 
                        and F.active = %s
                        and F.accepted = %s"""

        query_params.append(dados["recipient_users_fk"])

        query_params.append(dados["active"])

        query_params.append(dados["accepted"])

        conn = MySQLConnection()

        resultado = conn.execute(query, tuple(query_params))

        contagem = "SELECT COUNT(*) FROM (" + query + ") as users_contagem;"
        ocorrencias = conn.execute(contagem, tuple(query_params))[0][0]
        pagina_atual = int(dados["offset"] / dados["limit"]) + 1
        ultima_pagina = ceil(ocorrencias / dados["limit"])

        friends = []
        if resultado:
            for linha in resultado:
                aux_dict = {}
                for chave, valor in zip(CAMPOS, linha):
                    aux_dict[chave] = valor
                friends.append(aux_dict.copy())

        else:
            return {"message": "None country found with the required filters."}, 404

        retorno = {
            "friends": friends,
            "current_page": pagina_atual,
            "last_page": ultima_pagina,
        }

        return marshal(retorno, self.retorno_model), 200


@friends.route("/<int:friends_pk>/delete/")
class friendDelete(Resource):

    @jwt_required()
    def delete(self, friends_pk):
        try:
            friend = friendModel.find_by_pk(friends_pk)
            if friend:
                friend.delete()
                return {"message": "Friend successfully deleted"}, 200
            return {"message": "Friend not found."}, 404
        except:
            return {"message": "Internal server error"}, 500
