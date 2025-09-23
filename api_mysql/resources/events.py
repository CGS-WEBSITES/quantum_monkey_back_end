import traceback
from flask_restx import Resource, Namespace, reqparse, fields, marshal
from models.events import eventModel
from flask_jwt_extended import jwt_required
from sql_alchemy import MySQLConnection
from utils import dateTimeType, boolean_string
from pytz import timezone
from math import ceil
from datetime import datetime
from models.stores import StoreModel


event = Namespace("Events", "Events related Endpoints")


@event.route("/cadastro")
class eventRegister(Resource):

    atributos = reqparse.RequestParser()
    atributos.add_argument(
        "seats_number",
        type=int,
        required=True,
    )
    atributos.add_argument(
        "seasons_fk",
        type=int,
        required=True,
    )
    atributos.add_argument(
        "sceneries_fk",
        type=int,
        required=True,
    )
    atributos.add_argument(
        "date",
        type=dateTimeType,
        required=True,
    )
    atributos.add_argument(
        "stores_fk",
        type=int,
        required=True,
    )
    atributos.add_argument(
        "users_fk",
        type=int,
        required=True,
    )
    atributos.add_argument("active", type=bool, required=True, default=True)

    @event.expect(atributos, validate=True)
    @jwt_required()
    def post(self):
        dados = self.atributos.parse_args()

        store = StoreModel.find_store(dados["stores_fk"])

        if not store.active:
            return {"message": "This store is inactive."}, 403

        if not store.verified:
            return {"message": "Unverified stores can't create events."}, 403

        event = eventModel(**dados)
        try:
            event.save()

        except:
            event.remove()
            traceback.print_exc()
            return {"message": "Internal server error"}, 500

        return {
            "message": "event created successfully",
            "event": event.json(),
        }, 201  # Created


@event.route("/alter")
class eventAlter(Resource):

    atributos = reqparse.RequestParser()
    atributos.add_argument(
        "events_pk",
        type=int,
        required=True,
    )
    atributos.add_argument(
        "seats_number",
        type=int,
        required=False,
    )
    atributos.add_argument(
        "seasons_fk",
        type=int,
        required=False,
    )
    atributos.add_argument(
        "sceneries_fk",
        type=int,
        required=False,
    )
    atributos.add_argument(
        "date",
        type=dateTimeType,
        required=False,
    )
    atributos.add_argument(
        "stores_fk",
        type=int,
        required=False,
    )

    @jwt_required()
    @event.expect(atributos, validate=True)
    def put(self):
        kwargs = self.atributos.parse_args()
        event = eventModel.find_event(kwargs["events_pk"])

        store = StoreModel.find_store(kwargs["stores_fk"])

        if not store.active:
            return {"message": "This store is inactive."}, 403

        if not store.verified:
            return {"message": "Unverified stores can't create events."}, 403

        if event:
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


@event.route("/<int:events_pk>")
class eventGet(Resource):

    events_model = event.model(
        "Events Model",
        {
            "seats_number": fields.Integer(
                required=True,
                description="Total number of available seats for the event",
            ),
            "events_pk": fields.Integer(
                required=True, description="Primary key identifier of the event"
            ),
            "seasons_fk": fields.Integer(
                required=True,
                description="Identifier linking the event to a season or campaign in the data lake",
            ),
            "event_date": fields.DateTime(
                required=True, description="Scheduled date of the event"
            ),
            "scenario": fields.String(
                required=True,
                max_length=145,
                description="Name of the store or venue hosting the event",
            ),
            "store_name": fields.String(
                required=True,
                max_length=200,
                description="Name of the store or venue hosting the event",
            ),
            "picture_hash": fields.String(
                required=True,
                max_length=145,
                description="Name of the store or venue hosting the event",
            ),
            "address": fields.String(
                required=True,
                max_length=256,
                description="Human-readable status label of the event (e.g., Scheduled, Completed)",
            ),
            "latitude": fields.Float(
                required=False,
                description="Geographical latitude of the event location",
            ),
            "longitude": fields.Float(
                required=False,
                description="Geographical longitude of the event location",
            ),
        },
    )

    @event.marshal_with(events_model)
    def get(self, events_pk):

        CAMPOS = [
            "seats_number",
            "events_pk",
            "seasons_fk",
            "event_date",
            "scenario",
            "store_name",
            "picture_hash",
            "address",
            "latitude",
            "longitude",
        ]

        query = """SELECT
                    e.seats_number,
                    e.events_pk,
                    e.seasons_fk,
                    e.date AS event_date,
                    sc.name AS scenario,
                    s.name AS store_name,
                    s.picture_hash,
                    s.address,
                    s.latitude,
                    s.longitude
                FROM
                    events e
                LEFT JOIN sceneries sc ON
                    e.sceneries_fk = sc.sceneries_pk
                INNER JOIN stores s ON
                    e.stores_fk = s.stores_pk
                WHERE
                    e.events_pk = %s
                    AND e.active = true """

        query_params = []

        query_params.append(events_pk)

        conn = MySQLConnection()

        resultado = conn.execute(query, tuple(query_params))

        events = []
        if resultado:
            for linha in resultado:
                aux_dict = {}
                for chave, valor in zip(CAMPOS, linha):
                    aux_dict[chave] = valor
                events.append(aux_dict.copy())

        else:
            return {"message": "None event found with the required filters."}, 404

        return marshal(events, self.events_model), 200


@event.route("/list_events/")
class listEvents(Resource):

    events_model = event.model(
        "Events Model",
        {
            "seats_number": fields.Integer(
                required=True,
                description="Total number of available seats for the event",
            ),
            "events_pk": fields.Integer(
                required=True, description="Primary key identifier of the event"
            ),
            "seasons_fk": fields.Integer(
                required=True,
                description="Identifier linking the event to a season or campaign in the data lake",
            ),
            "event_date": fields.DateTime(
                required=True, description="Scheduled date of the event"
            ),
            "scenario": fields.String(
                required=True,
                max_length=145,
                description="Name of the store or venue hosting the event",
            ),
            "store_name": fields.String(
                required=True,
                max_length=200,
                description="Name of the store or venue hosting the event",
            ),
            "picture_hash": fields.String(
                required=True,
                max_length=145,
                description="Name of the store or venue hosting the event",
            ),
            "address": fields.String(
                required=True,
                max_length=256,
                description="Human-readable status label of the event (e.g., Scheduled, Completed)",
            ),
            "latitude": fields.Float(
                required=False,
                description="Geographical latitude of the event location",
            ),
            "longitude": fields.Float(
                required=False,
                description="Geographical longitude of the event location",
            ),
            "status": fields.String(
                required=True,
                max_length=200,
                description="Human-readable status label of the event (e.g., Scheduled, Completed)",
            ),
            "status_fk": fields.Integer(
                required=True, description="Foreign key referencing the status entity"
            ),
            "status_date": fields.Date(
                required=True, description="Date when the current status was set"
            ),
        },
    )

    retorno_model = event.model(
        "Search events Model",
        {
            "events": fields.List(fields.Nested(events_model)),
            "message": fields.String,
            "current_page": fields.Integer,
            "last_page": fields.Integer,
        },
    )

    parser = event.parser()
    parser.add_argument("player_fk", type=int, required=True)
    parser.add_argument("retailer_fk", type=int, required=False)
    parser.add_argument(
        "past_events", type=boolean_string, required=False, default="false"
    )
    parser.add_argument("limit", type=int, required=False, default=30)
    parser.add_argument("offset", type=int, required=False, default=0)

    @jwt_required()
    @event.expect(parser)
    @event.marshal_with(retorno_model)
    def get(self):

        CAMPOS = [
            "seats_number",
            "events_pk",
            "seasons_fk",
            "event_date",
            "scenario",
            "store_name",
            "picture_hash",
            "address",
            "latitude",
            "longitude",
            "status",
            "status_fk",
            "status_date",
        ]

        dados = self.parser.parse_args()

        query = """WITH ranked_reu AS (
                    SELECT
                        reu.events_fk,
                        reu.date,
                        reu.status,
                        ROW_NUMBER() OVER (PARTITION BY reu.events_fk
                    ORDER BY
                        reu.date DESC) AS rn
                    FROM
                        rl_events_users reu
                    WHERE
                        reu.users_fk = %s
                        AND reu.active = true
                    )
                    SELECT
                        e.seats_number,
                        e.events_pk,
                        e.seasons_fk,
                        e.date AS event_date,
                        sc.name AS scenario,
                        s.name AS store_name,
                        s.picture_hash,
                        s.address,
                        s.latitude,
                        s.longitude,
                        es.name AS status,
                        es.event_status_pk AS status_fk,
                        r.date AS status_date
                    FROM
                        events e
                    LEFT JOIN ranked_reu r ON
                        e.events_pk = r.events_fk
                        AND r.rn = 1 
                    LEFT JOIN sceneries sc ON
	                    e.sceneries_fk = sc.sceneries_pk """

        query_params = []

        query_params.append(dados["player_fk"])

        if dados["retailer_fk"]:

            query += """ LEFT JOIN event_status es ON
                            es.event_status_pk = r.status
                        INNER JOIN stores s ON
                            e.stores_fk = s.stores_pk
                        WHERE 
                            e.users_fk = %s
                            AND e.active = true """

            query_params.append(dados["retailer_fk"])

        else:
            query += """ LEFT JOIN event_status es ON
                            es.event_status_pk = r.status
                        INNER JOIN stores s ON
                            e.stores_fk = s.stores_pk
                        WHERE
                            e.active = true """

        if not dados["past_events"]:
            query += """ AND e.date >= %s
                    ORDER BY e.date """
            query_params.append(datetime.now(timezone("America/Sao_Paulo")).isoformat())

        else:
            query += """ ORDER BY e.date """

        conn = MySQLConnection()

        resultado = conn.execute(query, tuple(query_params))

        contagem = "SELECT COUNT(*) FROM (" + query + ") as users_contagem;"
        ocorrencias = conn.execute(contagem, tuple(query_params))[0][0]
        pagina_atual = int(dados["offset"] / dados["limit"]) + 1
        ultima_pagina = ceil(ocorrencias / dados["limit"])

        events = []
        if resultado:
            for linha in resultado:
                aux_dict = {}
                for chave, valor in zip(CAMPOS, linha):
                    aux_dict[chave] = valor
                events.append(aux_dict.copy())
            retorno = {
                "events": events,
                "current_page": pagina_atual,
                "message": "Events found!",
                "last_page": ultima_pagina,
            }

        else:
            retorno = {
                "events": events,
                "current_page": pagina_atual,
                "message": "None event found with the required filters.",
                "last_page": ultima_pagina,
            }

        return marshal(retorno, self.retorno_model), 200


@event.route("/my_events/player")
class playerEvents(Resource):

    events_model = event.model(
        "Events Model",
        {
            "seats_number": fields.Integer(
                required=True,
                description="Total number of available seats for the event",
            ),
            "events_pk": fields.Integer(
                required=True, description="Primary key identifier of the event"
            ),
            "seasons_fk": fields.Integer(
                required=True,
                description="Identifier linking the event to a season or campaign in the data lake",
            ),
            "event_date": fields.DateTime(
                required=True, description="Scheduled date of the event"
            ),
            "scenario": fields.String(
                required=True,
                max_length=145,
                description="Name of the store or venue hosting the event",
            ),
            "store_name": fields.String(
                required=True,
                max_length=200,
                description="Name of the store or venue hosting the event",
            ),
            "picture_hash": fields.String(
                required=True,
                max_length=145,
                description="Name of the store or venue hosting the event",
            ),
            "address": fields.String(
                required=True,
                max_length=256,
                description="Human-readable status label of the event (e.g., Scheduled, Completed)",
            ),
            "latitude": fields.Float(
                required=False,
                description="Geographical latitude of the event location",
            ),
            "longitude": fields.Float(
                required=False,
                description="Geographical longitude of the event location",
            ),
            "status": fields.String(
                required=True,
                max_length=200,
                description="Human-readable status label of the event (e.g., Scheduled, Completed)",
            ),
            "status_fk": fields.Integer(
                required=True, description="Foreign key referencing the status entity"
            ),
            "status_date": fields.Date(
                required=True, description="Date when the current status was set"
            ),
            "rl_events_users_pk": fields.Integer(
                required=True,
                description="Foreign key referencing theuser relationship",
            ),
        },
    )

    retorno_model = event.model(
        "Search events Model",
        {
            "events": fields.List(fields.Nested(events_model)),
            "message": fields.String,
            "current_page": fields.Integer,
            "last_page": fields.Integer,
        },
    )

    parser = event.parser()
    parser.add_argument("player_fk", type=int, required=True)
    parser.add_argument(
        "past_events", type=boolean_string, required=False, default="false"
    )
    parser.add_argument("limit", type=int, required=False, default=30)
    parser.add_argument("offset", type=int, required=False, default=0)

    @jwt_required()
    @event.expect(parser)
    @event.marshal_with(retorno_model)
    def get(self):

        CAMPOS = [
            "seats_number",
            "events_pk",
            "seasons_fk",
            "event_date",
            "scenario",
            "store_name",
            "picture_hash",
            "address",
            "latitude",
            "longitude",
            "status",
            "status_fk",
            "status_date",
            "rl_events_users_pk",
        ]

        dados = self.parser.parse_args()

        query = """ WITH ranked_statuses AS (
                        SELECT
                            reu.*,
                            ROW_NUMBER() OVER (
                                    PARTITION BY reu.users_fk,
                            reu.events_fk
                        ORDER BY
                            reu.date DESC
                                ) AS row_num
                        FROM
                            rl_events_users reu
                        WHERE
                            reu.active = true
                        )
                        SELECT
                            e.seats_number,
                            e.events_pk,
                            e.seasons_fk,
                            e.date AS event_date,
                            sc.name AS scenario,
                            s.name AS store_name,
                            s.picture_hash,
                            s.address,
                            s.latitude,
                            s.longitude,
                            es.name AS status,
                            es.event_status_pk AS status_fk,
                            reu.date AS status_date,
                            reu.rl_events_users_pk
                        FROM
                            ranked_statuses reu
                        LEFT JOIN events e ON
                            e.events_pk = reu.events_fk
                        LEFT JOIN sceneries sc ON
                            e.sceneries_fk = sc.sceneries_pk
                        LEFT JOIN event_status es ON
                            es.event_status_pk = reu.status
                        INNER JOIN stores s ON
                            e.stores_fk = s.stores_pk
                        WHERE
                            reu.users_fk = %s
                            AND row_num = 1
                            AND e.active = true """

        query_params = []

        query_params.append(dados["player_fk"])

        if not dados["past_events"]:
            query += """ AND e.date >= %s
                    ORDER BY e.date """
            query_params.append(datetime.now(timezone("America/Sao_Paulo")).isoformat())

        else:
            query += """ ORDER BY e.date """

        conn = MySQLConnection()

        resultado = conn.execute(query, tuple(query_params))

        contagem = "SELECT COUNT(*) FROM (" + query + ") as users_contagem;"
        ocorrencias = conn.execute(contagem, tuple(query_params))[0][0]
        pagina_atual = int(dados["offset"] / dados["limit"]) + 1
        ultima_pagina = ceil(ocorrencias / dados["limit"])

        events = []

        if resultado:
            for linha in resultado:
                aux_dict = {}
                for chave, valor in zip(CAMPOS, linha):
                    aux_dict[chave] = valor
                events.append(aux_dict.copy())

            retorno = {
                "events": events,
                "current_page": pagina_atual,
                "message": "Events found!",
                "last_page": ultima_pagina,
            }

        else:
            retorno = {
                "events": events,
                "current_page": pagina_atual,
                "message": "None event found with the required filters.",
                "last_page": ultima_pagina,
            }

        return marshal(retorno, self.retorno_model), 200


@event.route("/my_events/retailer")
class retailerEvents(Resource):

    events_model = event.model(
        "Events Model",
        {
            "seats_number": fields.Integer(
                required=True,
                description="Total number of available seats for the event",
            ),
            "events_pk": fields.Integer(
                required=True, description="Primary key identifier of the event"
            ),
            "seasons_fk": fields.Integer(
                required=True,
                description="Identifier linking the event to a season or campaign in the data lake",
            ),
            "event_date": fields.DateTime(
                required=True, description="Scheduled date and time of the event"
            ),
            "scenario": fields.String(
                required=True,
                max_length=145,
                description="Name of the store or venue hosting the event",
            ),
            "store_name": fields.String(
                required=True,
                max_length=200,
                description="Name of the store or venue hosting the event",
            ),
            "picture_hash": fields.String(
                required=True,
                max_length=145,
                description="Name of the store or venue hosting the event",
            ),
            "address": fields.String(
                required=False, description="Foreign key referencing the address entity"
            ),
            "latitude": fields.Float(
                required=False,
                description="Geographical latitude of the event location",
            ),
            "longitude": fields.Float(
                required=False,
                description="Geographical longitude of the event location",
            ),
        },
    )

    retorno_model = event.model(
        "Search events Model",
        {
            "events": fields.List(fields.Nested(events_model)),
            "message": fields.String,
            "current_page": fields.Integer,
            "last_page": fields.Integer,
        },
    )

    parser = event.parser()
    parser.add_argument("retailer_fk", type=int, required=True)
    parser.add_argument("active", type=boolean_string, required=False, default="true")
    parser.add_argument(
        "past_events", type=boolean_string, required=False, default="false"
    )
    parser.add_argument("limit", type=int, required=False, default=30)
    parser.add_argument("offset", type=int, required=False, default=0)

    @jwt_required()
    @event.expect(parser)
    @event.marshal_with(retorno_model)
    def get(self):
        now = datetime.now(timezone("America/Sao_Paulo"))

        CAMPOS = [
            "seats_number",
            "events_pk",
            "seasons_fk",
            "event_date",
            "scenario",
            "store_name",
            "picture_hash",
            "address",
            "latitude",
            "longitude",
        ]

        dados = self.parser.parse_args()

        query = """SELECT
                        e.seats_number,
                        e.events_pk,
                        e.seasons_fk,
                        e.date AS event_date,
                        sc.name AS scenario,
                        s.name AS store_name,
                        s.picture_hash,
                        s.address,
                        s.latitude,
                        s.longitude
                    FROM
                        events e
                    INNER JOIN stores s ON
                        e.stores_fk = s.stores_pk
                    LEFT JOIN sceneries sc ON
	                    e.sceneries_fk = sc.sceneries_pk
                    WHERE
                        e.users_fk = %s
                        AND e.active = %s """

        query_params = []

        query_params.append(dados["retailer_fk"])
        query_params.append(dados["active"])

        if not dados["past_events"]:
            query += """ AND e.date >= %s
                    ORDER BY e.date """
            query_params.append(datetime.now(timezone("America/Sao_Paulo")).isoformat())

        else:
            query += """ ORDER BY e.date """

        conn = MySQLConnection()

        resultado = conn.execute(query, tuple(query_params))

        contagem = "SELECT COUNT(*) FROM (" + query + ") as users_contagem;"
        ocorrencias = conn.execute(contagem, tuple(query_params))[0][0]
        pagina_atual = int(dados["offset"] / dados["limit"]) + 1
        ultima_pagina = ceil(ocorrencias / dados["limit"])

        events = []
        if resultado:
            for linha in resultado:
                aux_dict = {}
                for chave, valor in zip(CAMPOS, linha):
                    aux_dict[chave] = valor
                events.append(aux_dict.copy())

            retorno = {
                "events": events,
                "current_page": pagina_atual,
                "message": "Events found!",
                "last_page": ultima_pagina,
            }

        else:
            retorno = {
                "events": events,
                "current_page": pagina_atual,
                "message": "None event found with the required filters.",
                "last_page": ultima_pagina,
            }

        return marshal(retorno, self.retorno_model), 200


@event.route("/<int:events_pk>/delete/")
class eventDelete(Resource):

    @jwt_required()
    def delete(self, events_pk):
        try:
            event = eventModel.find_event(events_pk)
            if event:
                event.delete()
                return {"message": "event successfully deleted"}, 200
            return {"message": "event not found."}, 404
        except:
            return {"message": "Internal server error"}, 500
