import traceback
import requests
from flask_restx import Resource, Namespace, reqparse, fields, marshal
from models.stores import StoreModel
from flask_jwt_extended import jwt_required
from sql_alchemy import MySQLConnection
from pytz import timezone
from utils import boolean_string
from math import ceil
import requests
from config import GOOGLE_API_KEY
from email_sender import send_store_verification_email, send_store_denial_email


store = Namespace("Stores", "Stores related Endpoints")


@store.route("/cadastro")
class storeRegister(Resource):

    atributos = reqparse.RequestParser()
    atributos.add_argument("site", type=str, required=False)
    atributos.add_argument("name", type=str, required=True)
    atributos.add_argument("zip_code", type=str, required=True)
    atributos.add_argument("countries_fk", type=int, required=True)
    atributos.add_argument("users_fk", type=int, required=True)
    atributos.add_argument("address", type=str, required=True)
    atributos.add_argument("latitude", type=float, required=False)
    atributos.add_argument("longitude", type=float, required=False)
    atributos.add_argument("picture_hash", type=str, required=False)
    atributos.add_argument("web_site", type=str, required=False)
    atributos.add_argument("state", type=str, required=False)
    atributos.add_argument("merchant_id", type=str, required=False)
    atributos.add_argument(
        "verified", type=boolean_string, required=False, default=False
    )
    atributos.add_argument("active", type=boolean_string, required=False, default=True)

    @store.expect(atributos, validate=True)
    @jwt_required()
    def post(self):
        dados = self.atributos.parse_args()

        store = StoreModel(**dados)
        try:
            store.save()
        except:
            store.remove_store()
            traceback.print_exc()
            return {"message": "Internal server error"}, 500

        try:
            print(
                f"Store created successfully. Attempting to send verification email for store ID: {store.stores_pk}"
            )
            send_store_verification_email(store.json())
        except Exception as e:
            print(
                "--- WARNING: Store was created, but verification email failed to send. ---"
            )
            traceback.print_exc()
            print("--- END OF EMAIL ERROR ---")

        return {
            "message": "Store created successfully. Verification process initiated.",
            "store": store.json(),
        }, 201


@store.route("/list")
class storeList(Resource):

    stores_model = store.model(
        "Store Model",
        {
            "stores_pk": fields.Integer(required=True, description="Relationship key"),
            "site": fields.String(
                required=False, max_length=145, description="Nickname"
            ),
            "name": fields.String(
                required=False, max_length=145, description="Nickname"
            ),
            "zip_code": fields.String(
                required=False, max_length=145, description="Nickname"
            ),
            "countries_fk": fields.Integer(required=True, description="Recipient key"),
            "users_fk": fields.Integer(
                required=True, description="User role in the system"
            ),
            "address": fields.String(
                required=False, max_length=256, description="address"
            ),
            "longitude": fields.Float(required=False, description="longitude"),
            "latitude": fields.Float(required=False, description="longitude"),
            "picture_hash": fields.String(
                required=False, max_length=145, description="picture_hash"
            ),
            "web_site": fields.String(
                required=False, max_length=145, description="web_site"
            ),
            "state": fields.String(required=False, max_length=100, description="state"),
            "merchant_id": fields.String(
                required=False, max_length=200, description="state"
            ),
            "verified": fields.Boolean(
                required=True, description="Is this relation accepted"
            ),
            "active": fields.Boolean(
                required=True, description="Is this relation accepted"
            ),
        },
    )

    retorno_model = store.model(
        "Search store Model",
        {
            "stores": fields.List(fields.Nested(stores_model)),
            "current_page": fields.Integer,
            "last_page": fields.Integer,
        },
    )

    parser = store.parser()
    parser.add_argument("users_fk", type=int, required=True)
    parser.add_argument("verified", type=boolean_string, required=False)
    parser.add_argument("active", type=boolean_string, required=False, default=True)
    parser.add_argument("limit", type=int, required=False, default=30)
    parser.add_argument("offset", type=int, required=False, default=0)

    @jwt_required()
    @store.expect(parser)
    @store.marshal_with(retorno_model)
    def get(self):
        CAMPOS = [
            "stores_pk",
            "site",
            "name",
            "zip_code",
            "countries_fk",
            "users_fk",
            "address",
            "longitude",
            "latitude",
            "picture_hash",
            "web_site",
            "state",
            "merchant_id",
            "verified",
            "active",
        ]

        dados = self.parser.parse_args()

        query = """SELECT
                        stores_pk,
                        site,
                        name,
                        zip_code,
                        countries_fk,
                        users_fk,
                        address,
                        longitude,
                        latitude,
                        picture_hash,
                        web_site,
                        state,
                        merchant_id,
                        verified,
                        active
                    FROM
                        stores """

        query_params = []

        query += """WHERE
                        users_fk = %s 
                        and active = %s """
        query_params.append(dados["users_fk"])
        query_params.append(dados["active"])

        if dados["verified"]:
            query += """and verified = %s"""
            query_params.append(dados["verified"])

        conn = MySQLConnection()
        resultado = conn.execute(query, tuple(query_params))

        contagem = "SELECT COUNT(*) FROM (" + query + ") as users_contagem;"
        ocorrencias = conn.execute(contagem, tuple(query_params))[0][0]
        pagina_atual = int(dados["offset"] / dados["limit"]) + 1
        ultima_pagina = ceil(ocorrencias / dados["limit"])

        stores = []
        if resultado and len(resultado) != 0:
            for linha in resultado:
                aux_dict = {}
                for chave, valor in zip(CAMPOS, linha):
                    aux_dict[chave] = valor
                stores.append(aux_dict.copy())
        else:
            return {"message": "None country found with the required filters."}, 404

        retorno = {
            "stores": stores,
            "current_page": pagina_atual,
            "last_page": ultima_pagina,
        }

        return marshal(retorno, self.retorno_model), 200


@store.route("/alter")
class storeAlter(Resource):

    atributos = reqparse.RequestParser()
    atributos.add_argument("stores_pk", type=int, required=True)
    atributos.add_argument("site", type=str, required=False)
    atributos.add_argument("name", type=str, required=False)
    atributos.add_argument("zip_code", type=str, required=False)
    atributos.add_argument("countries_fk", type=int, required=False)
    atributos.add_argument("address", type=str, required=False)
    atributos.add_argument("latitude", type=float, required=False)
    atributos.add_argument("longitude", type=float, required=False)
    atributos.add_argument("picture_hash", type=str, required=False)
    atributos.add_argument("web_site", type=str, required=False)
    atributos.add_argument("merchant_id", type=str, required=False)
    atributos.add_argument("state", type=str, required=False)

    @jwt_required()
    @store.expect(atributos, validate=True)
    def put(self):
        kwargs = self.atributos.parse_args()
        store = StoreModel.find_store(kwargs["stores_pk"])

        if store:
            try:
                store.update(**kwargs)
                return {
                    "message": "store has been altered successfully.",
                    "data": store.json(),
                }, 200
            except:
                traceback.print_exc()
                return {"message": "Internal server error"}, 500

        return {"message": "store not found."}, 404


@store.route("/<int:stores_pk>")
class storeGet(Resource):

    @jwt_required()
    def get(self, stores_pk):
        store = StoreModel.find_store(stores_pk)

        if store:
            return store.json(), 200

        return {"message": "store not found."}, 404


@store.route("/<int:stores_pk>/delete/")
class storeDelete(Resource):

    @jwt_required()
    def delete(self, stores_pk):
        try:
            store = StoreModel.find_store(stores_pk)
            if store:
                store.delete()

                query = """UPDATE
                            events
                        SET
                            active = 0
                        WHERE
                            stores_fk = %s"""

                query_params = [stores_pk]

                try:
                    with MySQLConnection() as conn:
                        result = conn.mutate(query, tuple(query_params))
                except:
                    return {"message": "Error deleting events"}, 200

                return {
                    "message": "Store successfully deleted. {} events where deleted in the process.".format(
                        result
                    )
                }, 200

            return {"message": "store not found."}, 404
        except:
            return {"message": "Internal server error"}, 500


@store.route("/<int:stores_pk>/verify")
class storeVerify(Resource):

    def get(self, stores_pk):
        store = StoreModel.find_store(stores_pk)

        if store:
            try:
                try:
                    encoded_address = requests.utils.quote(store.address)

                    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={encoded_address}&key={GOOGLE_API_KEY}"

                    response = requests.get(url)

                    data = response.json()

                    if data["status"] == "OK" and data["results"]:
                        location = data["results"][0]["geometry"]["location"]

                        store.latitude = location["lat"]

                        store.longitude = location["lng"]

                    else:
                        return {"message": "Adress not found"}, 404

                except Exception as e:
                    return {
                        "message": "Error when finding adrress: " + e,
                    }, 500

                store.verify()

                return {
                    "message": "store has been verified successfully.",
                    "data": store.json(),
                }, 200

            except:
                traceback.print_exc()

                return {"message": "Internal server error"}, 500

        return {"message": "store not found."}, 404
    
@store.route("/<int:stores_pk>/deny")
class storeDeny(Resource):
    def get(self, stores_pk):
        store = StoreModel.find_store(stores_pk)

        if store:
            try:
                send_store_denial_email(store.json())
                return {"message": f"Denial email successfully sent for store '{store.name}'."}, 200
            except Exception as e:
                traceback.print_exc()
                return {"message": f"An error occurred while sending the denial email: {e}"}, 500
        
        return {"message": "Store not found."}, 404