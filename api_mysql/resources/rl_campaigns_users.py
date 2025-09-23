import traceback
from flask_restx import Resource, Namespace, reqparse, fields, marshal
from models.rl_campaigns_users import RlCampaignsUsersModel
from flask_jwt_extended import jwt_required
from sql_alchemy import MySQLConnection
from datetime import datetime
from pytz import timezone
from utils import boolean_string


relationship = Namespace(
    "User Campaign Relationship", "campaigns relationships related Endpoints"
)


@relationship.route("/cadastro")
class CampaignRegister(Resource):

    atributos = reqparse.RequestParser()
    atributos.add_argument(
        "users_fk",
        type=int,
        required=True,
    )
    atributos.add_argument(
        "campaigns_fk",
        type=int,
        required=True,
    )
    atributos.add_argument(
        "party_roles_fk",
        type=int,
        required=True,
    )
    atributos.add_argument(
        "skus_fk",
        type=int,
        required=True,
    )
    atributos.add_argument("active", type=bool, required=False, default=True),

    @relationship.expect(atributos, validate=True)
    @jwt_required()
    def post(self):
        dados = self.atributos.parse_args()
        date = datetime.now(timezone("America/Sao_Paulo"))
        dados["start_date"] = date

        rl_campaign = RlCampaignsUsersModel(**dados)

        try:
            rl_campaign.save()

        except:
            return {"message": "Internal server error"}, 500

        return {
            "message": "rl_campaigns_users created successfully",
            "rl_campaigns_users": rl_campaign.json(),
        }, 201  # Created


@relationship.route("/search")
class campaignSearch(Resource):
    campaign_model = relationship.model(
        "campaigns Model",
        {
            "campaigns_fk": fields.Integer(required=True, description="campaign key"),
            "tracker_hash": fields.String(
                required=True, max_length=5000, description="campaign name"
            ),
            "start_date": fields.DateTime(required=True, description="Start date"),
            "conclusion_percentage": fields.Integer(
                required=False, description="campaign conclusion percentage."
            ),
            "party_name": fields.String(
                required=True, max_length=45, description="party name"
            ),
            "party_role": fields.String(
                required=True, max_length=45, description="party role"
            ),
            "box": fields.Integer(required=False, description="campaign box"),
            "active": fields.Boolean(
                required=True, description="campaign is visible for campaigns?"
            ),
        },
    )

    retorno_model = relationship.model(
        "Search campaign Model",
        {
            "campaigns": fields.List(fields.Nested(campaign_model)),
        },
    )

    parser = relationship.parser()
    parser.add_argument("users_fk", type=int, required=True)
    parser.add_argument("campaigns_fk", type=int, required=False)
    parser.add_argument("conclusion_percentage", type=int, required=False)
    parser.add_argument("party_name", type=str, required=False)
    parser.add_argument("box", type=str, required=False)
    parser.add_argument("active", type=boolean_string, required=False, default=True)

    @jwt_required()
    @relationship.expect(parser)
    @relationship.marshal_with(retorno_model)
    def get(self):
        CAMPOS = [
            "campaigns_fk",
            "tracker_hash",
            "start_date",
            "conclusion_percentage",
            "party_name",
            "party_role",
            "box",
            "active",
        ]
        dados = self.parser.parse_args()

        query = """SELECT
                        rl.campaigns_fk,
                        c.tracker_hash,
                        rl.start_date,
                        c.conclusion_percentage,
                        c.party_name,
                        r.name as 'party_role',
                        c.box,
                        rl.active
                    FROM
                        rl_campaigns_users rl
                    INNER JOIN campaigns c ON
                        c.campaigns_pk = rl.campaigns_fk
                    LEFT JOIN roles r ON
                        rl.party_roles_fk = r.roles_pk """

        query_params = []

        query += "WHERE rl.users_fk = %s "
        query_params.append(dados["users_fk"])

        if dados["campaigns_fk"]:
            query += "AND c.campaigns_pk = %s "
            query_params.append(dados["campaigns_fk"])

        if dados["conclusion_percentage"]:
            query += "AND c.conclusion_percentage = %s "
            query_params.append(dados["conclusion_percentage"])

        if dados["party_name"]:
            query += "AND c.party_name = %s "
            query_params.append(dados["party_name"])

        if dados["box"]:
            query += "AND c.box = %s "
            query_params.append(dados["box"])

        query += "AND rl.active = %s "

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


@relationship.route("/list_players")
class campaignListPlayers(Resource):
    campaign_model = relationship.model(
        "Users Model",
        {
            "rl_campaigns_users_pk": fields.Integer(
                required=False, description="campaign box"
            ),
            "user_name": fields.String(
                required=True, max_length=45, description="campaign name"
            ),
            "picture_hash": fields.String(
                required=True, max_length=200, description="campaign name"
            ),
            "background_hash": fields.String(
                required=True, max_length=200, description="campaign name"
            ),
            "party_roles_fk": fields.Integer(
                required=False, description="campaign box"
            ),
            "role_name": fields.String(
                required=True, max_length=200, description="campaign name"
            ),
        },
    )

    retorno_model = relationship.model(
        "List Users Model",
        {
            "Users": fields.List(fields.Nested(campaign_model)),
        },
    )

    parser = relationship.parser()
    parser.add_argument("campaigns_fk", type=int, required=False)
    parser.add_argument("active", type=boolean_string, required=False, default=True)

    @jwt_required()
    @relationship.expect(parser)
    # @relationship.marshal_with(retorno_model)
    def get(self):
        CAMPOS = [
            "rl_campaigns_users_pk",
            "user_name",
            "picture_hash",
            "background_hash",
            "party_roles_fk",
            "role_name"
        ]

        dados = self.parser.parse_args()

        query = """SELECT
                        rl.rl_campaigns_users_pk,
                        u.user_name,
                        u.picture_hash,
                        u.background_hash,
                        rl.party_roles_fk,
                        pr.name as 'role_name'
                    FROM
                        rl_campaigns_users rl
                    LEFT JOIN users u ON
                        u.users_pk = rl.users_fk
                    LEFT JOIN party_roles pr ON
                        rl.party_roles_fk = pr.party_roles_pk
                    WHERE
                        rl.campaigns_fk = %s
                        AND rl.active = %s """

        query_params = [dados["campaigns_fk"], dados["active"]]

        conn = MySQLConnection()

        resultado = conn.execute(query, tuple(query_params))

        # return {"resultado": resultado}

        # return {"query": query, "query_params": query_params}

        users = []
        if resultado:
            for linha in resultado:
                aux_dict = {}
                for chave, valor in zip(CAMPOS, linha):
                    aux_dict[chave] = valor
                users.append(aux_dict.copy())

        retorno = {
            "Users": users,
        }

        return marshal(retorno, self.retorno_model), 200


@relationship.route("/alter")
class CampaignAlter(Resource):

    atributos = reqparse.RequestParser()
    atributos.add_argument(
        "rl_campaigns_users_pk",
        type=int,
        required=True,
    ),
    atributos.add_argument(
        "users_fk",
        type=int,
        required=False,
    )
    atributos.add_argument(
        "campaigns_fk",
        type=int,
        required=False,
    )
    atributos.add_argument(
        "party_roles_fk",
        type=int,
        required=False,
    )
    atributos.add_argument(
        "skus_fk",
        type=int,
        required=False,
    )

    @jwt_required()
    @relationship.expect(atributos, validate=True)
    def put(self):

        kwargs = self.atributos.parse_args()
        rl_campaign = RlCampaignsUsersModel.find(kwargs["rl_campaigns_users_pk"])

        if rl_campaign:
            try:
                rl_campaign.update(**kwargs)

                return {
                    "message": "campaign has been altered successfully.",
                    "data": rl_campaign.json(),
                }, 200

            except:
                traceback.print_exc()
                return {"message": "Internal server error"}, 500

        return {"message": "campaign not found."}, 404


@relationship.route("/<int:rl_campaigns_users_pk>")
class CampaignGet(Resource):

    @jwt_required()
    def get(self, rl_campaigns_users_pk):
        rl_campaign = RlCampaignsUsersModel.find(rl_campaigns_users_pk)

        if rl_campaign:
            return rl_campaign.json(), 200

        return {"message": "campaign not found."}, 404  # not found


@relationship.route("/<int:rl_campaigns_users_pk>/delete/")
class CampaignDelete(Resource):

    @jwt_required()
    def delete(self, rl_campaigns_users_pk):
        try:
            rl_campaign = RlCampaignsUsersModel.find(rl_campaigns_users_pk)
            if rl_campaign:
                rl_campaign.delete()
                return {"message": "campaign successfully deleted"}, 200
            return {"message": "campaign not found."}, 404
        except:
            return {"message": "Internal server error"}, 500
