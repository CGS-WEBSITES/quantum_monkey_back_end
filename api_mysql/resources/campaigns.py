import traceback
from flask_restx import Resource, Namespace, reqparse, fields, marshal
from models.campaigns import CampaignModel
from flask_jwt_extended import jwt_required
from sql_alchemy import MySQLConnection
from datetime import datetime
from pytz import timezone
from utils import boolean_string


campaign = Namespace("Campaigns", "campaigns related Endpoints")


@campaign.route("/cadastro")
class CampaignRegister(Resource):

    atributos = reqparse.RequestParser()
    atributos.add_argument(
        "tracker_hash",
        type=str,
        required=True,
    ),
    atributos.add_argument(
        "conclusion_percentage",
        type=int,
        required=True,
    ),
    atributos.add_argument(
        "party_name",
        type=str,
        required=False,
    ),
    atributos.add_argument(
        "box",
        type=str,
        required=True,
    ),
    atributos.add_argument("active", type=bool, required=False, default=True),

    @campaign.expect(atributos, validate=True)
    @jwt_required()
    def post(self):
        dados = self.atributos.parse_args()

        campaign = CampaignModel(**dados)
        try:
            campaign.save()

        except:
            campaign.remove()
            traceback.print_exc()
            return {"message": "Internal server error"}, 500

        return {
            "message": "campaign created successfully",
            "campaign": campaign.json(),
        }, 201  # Created


@campaign.route("/search")
class campaignSearch(Resource):
    campaign_model = campaign.model(
        "campaigns Model",
        {
            "campaigns_pk": fields.Integer(required=True, description="campaign key"),
            "tracker_hash": fields.String(
                required=True, max_length=5000, description="campaign name"
            ),
            "conclusion_percentage": fields.Integer(
                required=False, description="campaign conclusion percentage."
            ),
            "party_name": fields.String(
                required=True, max_length=45, description="party name"
            ),
            "box": fields.String(
                required=False, max_length=45, description="campaign box"
            ),
            "active": fields.Boolean(
                required=True, description="campaign is visible for campaigns?"
            ),
        },
    )

    retorno_model = campaign.model(
        "Search campaign Model",
        {
            "campaigns": fields.List(fields.Nested(campaign_model)),
        },
    )

    parser = campaign.parser()
    parser.add_argument("conclusion_percentage", type=int, required=False)
    parser.add_argument("party_name", type=str, required=False)
    parser.add_argument("box", type=str, required=False)
    parser.add_argument("active", type=boolean_string, required=False, default=True)

    @jwt_required()
    @campaign.expect(parser)
    @campaign.marshal_with(retorno_model)
    def get(self):
        CAMPOS = [
            "campaigns_pk",
            "tracker_hash",
            "conclusion_percentage",
            "party_name",
            "box",
            "active",
        ]
        dados = self.parser.parse_args()

        query = """SELECT 
            campaigns_pk,
            tracker_hash,
            conclusion_percentage,
            party_name,
            box,
            active, FROM campaigns"""
        query_params = []

        if dados["conclusion_percentage"]:
            query += "WHERE conclusion_percentage =%d"
            query_params.append(dados["conclusion_percentage"])
            where = True

        if dados["party_name"]:
            if where:
                query += "AND party_name = %s"
            else:
                query += "WHERE party_name = %s"
                where = True

            query_params.append(dados["party_name"])

        if dados["box"]:
            if where:
                query += "AND party_name = %s"
            else:
                query += "WHERE party_name = %s"
                where = True

            query_params.append(dados["box"])

        if where:
            query += "AND active = %s"
        else:
            query += "WHERE active = %s"

        query_params.append(dados["active"])

        conn = MySQLConnection()
        resultado = conn.execute(query, tuple(query_params))

        campaigns = []
        if resultado:
            for linha in resultado:
                aux_dict = {}
                for chave, valor in zip(CAMPOS, linha):
                    aux_dict[chave] = valor
                campaigns.append(aux_dict.copy())

        retorno = {
            "campaigns": campaigns,
        }

        return marshal(retorno, self.retorno_model), 200


@campaign.route("/alter/<int:campaigns_pk>")
class CampaignAlter(Resource):

    atributos = reqparse.RequestParser()
    atributos.add_argument(
        "tracker_hash",
        type=str,
        required=False,
    ),
    atributos.add_argument(
        "party_name",
        type=str,
        required=False,
    ),

    @jwt_required()
    @campaign.expect(atributos, validate=True)
    def put(self, campaigns_pk):
        campaign = CampaignModel.find_campaign(campaigns_pk)
        if campaign:
            kwargs = self.atributos.parse_args()

            try:
                campaign.update(**kwargs)

                return {
                    "message": "campaign has been altered successfully.",
                    "data": campaign.json(),
                }, 200

            except:
                traceback.print_exc()
                return {"message": "Internal server error"}, 500

        return {"message": "campaign not found."}, 404


@campaign.route("/<int:campaigns_pk>")
class CampaignGet(Resource):

    @jwt_required()
    def get(self, campaigns_pk):
        campaign = CampaignModel.find_campaign(campaigns_pk)

        if campaign:
            return campaign.json(), 200

        return {"message": "campaign not found."}, 404  # not found


@campaign.route("/<int:campaigns_pk>/delete/")
class CampaignDelete(Resource):

    @jwt_required()
    def delete(self, campaigns_pk):
        try:
            campaign = CampaignModel.find_campaign(campaigns_pk)
            if campaign:
                campaign.delete()

                query = """UPDATE
                            rl_campaigns_users
                        SET
                            active = 0
                        WHERE
                            campaigns_fk = %s"""

                query_params = [campaigns_pk]

                try:
                    with MySQLConnection() as conn:
                        result = conn.mutate(query, tuple(query_params))
                except:
                    return {"message": "Error deleting relationships"}, 200

                return {
                    "message": "Campaign successfully deleted. {} relationships where deleted in the process.".format(
                        result
                    )
                }, 200

            return {"message": "campaign not found."}, 404
        except:
            return {"message": "Internal server error"}, 500
