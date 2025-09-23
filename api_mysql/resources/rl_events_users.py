import traceback
from flask_restx import Resource, Namespace, reqparse, fields, marshal
from models.rl_events_users import rlEventsUsersModel
from flask_jwt_extended import jwt_required
from sql_alchemy import MySQLConnection
from datetime import datetime
from pytz import timezone
from math import ceil

rl_events_users = Namespace(
    "User Event Relationship", "events relationships related Endpoints"
)


@rl_events_users.route("/cadastro")
class eventRegister(Resource):

    atributos = reqparse.RequestParser()
    atributos.add_argument(
        "users_fk",
        type=int,
        required=True,
    )
    atributos.add_argument(
        "events_fk",
        type=int,
        required=True,
    )
    atributos.add_argument(
        "status",
        type=int,
        required=True,
    )
    atributos.add_argument("active", type=bool, required=False, default=True),

    @rl_events_users.expect(atributos, validate=True)
    @jwt_required()
    def post(self):
        dados = self.atributos.parse_args()
        date = datetime.now(timezone("America/Sao_Paulo"))
        dados["date"] = date

        relationship = rlEventsUsersModel(**dados)

        query = """ SELECT
                        COUNT(CASE WHEN rl.users_fk = %s AND rl.status = 1 THEN 1 END) AS count_requests,
                        COUNT(CASE WHEN rl.status = 2 THEN 1 END) AS count_accepted,
                        e.seats_number
                    FROM
                        rl_events_users rl
                    LEFT JOIN events e ON e.events_pk = rl.events_fk
                    WHERE
                        events_fk = %s """

        query_params = [dados["users_fk"], dados["events_fk"]]

        conn = MySQLConnection()

        resultado = conn.execute(query, tuple(query_params))

        if dados["status"] <= 3 and resultado[0][2]:
            if resultado[0][0] != 0 and dados["status"] == 1:
                return {
                    "message": "The player has already signed up for the event.",
                }, 400

            elif resultado[0][1] >= resultado[0][2]:
                return {
                    "message": "All the seats for the event have already been taken",
                }, 400

        try:
            relationship.save()

        except:
            return {"message": "Internal server error"}, 500

        return {
            "message": "rl_events_users created successfully",
            "rl_events_users": relationship.json(),
        }, 201  # Created


@rl_events_users.route("/alter/<int:rl_events_users_pk>")
class eventAlter(Resource):

    atributos = reqparse.RequestParser()
    atributos.add_argument(
        "status",
        type=str,
        required=False,
    )
    atributos.add_argument("active", type=bool, required=False, default=True),

    @jwt_required()
    @rl_events_users.expect(atributos, validate=True)
    def put(self, rl_events_users_pk):
        event = rlEventsUsersModel.find(rl_events_users_pk)
        if event:
            kwargs = self.atributos.parse_args()

            date = datetime.now(timezone("America/Sao_Paulo"))
            kwargs["date"] = date

            try:
                event.update(**kwargs)

                return {
                    "message": "event has been altered successfully.",
                    "data": event.json(),
                }, 200

            except:
                traceback.print_exc()
                return {"message": "Internal server error"}, 500

        return {"message": "event not found."}, 404


@rl_events_users.route("/<int:events_pk>")
class eventGet(Resource):

    @jwt_required()
    def get(self, events_pk):
        relationship = rlEventsUsersModel.find_event(events_pk)

        if relationship:
            return relationship.json(), 200

        return {"message": "event not found."}, 404  # not found


@rl_events_users.route("/list_players")
class listPlayers(Resource):

    rl_events_users_model = rl_events_users.model(
        "Relationship Model",
        {
            "status_date": fields.DateTime(
                required=True, description="Relationship key"
            ),
            "rl_events_users_pk": fields.Integer(
                required=True, description="Figure id in data lake"
            ),
            "event_status": fields.String(
                required=True, max_length=200, description="Figure id in data lake"
            ),
            "users_pk": fields.Integer(
                required=True, description="Figure id in data lake"
            ),
            "user_name": fields.String(
                required=True, max_length=200, description="Figure id in data lake"
            ),
            "email": fields.String(
                required=True, max_length=320, description="Figure id in data lake"
            ),
            "picture_hash": fields.String(
                required=True, max_length=200, description="Figure id in data lake"
            ),
            "background_hash": fields.String(
                required=True, max_length=200, description="Figure id in data lake"
            ),
            "country_abb": fields.String(
                required=True, max_length=3, description="Figure id in data lake"
            ),
            "country": fields.String(
                required=True, max_length=145, description="Figure id in data lake"
            ),
        },
    )

    retorno_model = rl_events_users.model(
        "List Relationship Model",
        {
            "players": fields.List(fields.Nested(rl_events_users_model)),
            "current_page": fields.Integer,
            "last_page": fields.Integer,
        },
    )

    parser = rl_events_users.parser()
    parser.add_argument("events_fk", type=int, required=True)
    parser.add_argument("limit", type=int, required=False, default=30)
    parser.add_argument("offset", type=int, required=False, default=0)

    @jwt_required()
    @rl_events_users.expect(parser)
    @rl_events_users.marshal_with(retorno_model)
    def get(self):

        CAMPOS = [
            "status_date",
            "rl_events_users_pk",
            "event_status",
            "users_pk",
            "user_name",
            "email",
            "picture_hash",
            "background_hash",
            "country_abb",
            "country",
        ]

        dados = self.parser.parse_args()

        query = """WITH latest_status_per_user AS (
                        SELECT
                            reu.users_fk,
                            MAX(reu.date) AS latest_date
                        FROM
                            rl_events_users reu
                        WHERE
                            reu.events_fk = %s
                            AND reu.active = true
                        GROUP BY
                            reu.users_fk
                        )
                        SELECT
                            reu.date AS status_date,
                            reu.rl_events_users_pk,
                            es.name AS event_status,
                            u.users_pk,
                            u.user_name,
                            u.email,
                            u.picture_hash,
                            u.background_hash,
                            c.abbreviation AS country_abb,
                            c.name AS country
                        FROM
                            rl_events_users reu
                        INNER JOIN latest_status_per_user lspu
                            ON
                            reu.users_fk = lspu.users_fk
                            AND reu.date = lspu.latest_date
                        LEFT JOIN event_status es ON
                            reu.status = es.event_status_pk
                        LEFT JOIN users u ON
                            reu.users_fk = u.users_pk
                        LEFT JOIN countries c ON
                            u.countries_fk = c.countries_pk """

        query_params = []

        query_params.append(dados["events_fk"])

        conn = MySQLConnection()

        resultado = conn.execute(query, tuple(query_params))

        contagem = "SELECT COUNT(*) FROM (" + query + ") as users_contagem;"
        ocorrencias = conn.execute(contagem, tuple(query_params))[0][0]
        pagina_atual = int(dados["offset"] / dados["limit"]) + 1
        ultima_pagina = ceil(ocorrencias / dados["limit"])

        players = []
        if resultado:
            for linha in resultado:
                aux_dict = {}
                for chave, valor in zip(CAMPOS, linha):
                    aux_dict[chave] = valor
                players.append(aux_dict.copy())

        else:
            return {"message": "None country found with the required filters."}, 404

        retorno = {
            "players": players,
            "current_page": pagina_atual,
            "last_page": ultima_pagina,
        }

        return marshal(retorno, self.retorno_model), 200


@rl_events_users.route("/<int:rl_events_users_pk>/delete/")
class eventDelete(Resource):
    @jwt_required()
    def delete(self, rl_events_users_pk):
        try:
            rl_events_users = rlEventsUsersModel.find(rl_events_users_pk)

            if rl_events_users:
                rl_events_users.delete()

                return {"message": "event successfully deleted"}, 200

            return {"message": "event not found."}, 404

        except:
            return {"message": "Internal server error"}, 500


@rl_events_users.route("/quit_event")
class eventQuit(Resource):

    parser = rl_events_users.parser()
    parser.add_argument("users_fk", type=int, required=True)
    parser.add_argument("events_fk", type=int, required=True)
    parser.add_argument

    @jwt_required()
    @rl_events_users.expect(parser)
    def delete(self):

        dados = self.parser.parse_args()

        query = """ SELECT
                        reu.rl_events_users_pk
                    FROM
                        rl_events_users reu
                    WHERE
                        reu.users_fk = %s 
                    AND reu.events_fk = %s """

        query_params = [dados["users_fk"], dados["events_fk"]]

        conn = MySQLConnection()

        resultado = conn.execute(query, tuple(query_params))

        try:
            for rl in resultado:
                rl_events_users = rlEventsUsersModel.find(rl[0])

                if rl_events_users:
                    rl_events_users.remove()

            return {"message": "event successfully quited"}, 200

        except:
            return {"message": "Internal server error"}, 500
