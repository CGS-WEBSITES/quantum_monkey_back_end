import traceback
from flask_restx import Resource, Namespace, reqparse, fields, marshal
from models.rl_users_rewards import rlUsersRewardsModel
from flask_jwt_extended import jwt_required
from sql_alchemy import MySQLConnection
from datetime import datetime
from pytz import timezone

rl_users_rewards = Namespace(
    "User Rewards Relationship", "Users relationships related Endpoints"
)


@rl_users_rewards.route("/cadastro")
class userRegister(Resource):

    atributos = reqparse.RequestParser()
    atributos.add_argument(
        "users_fk",
        type=int,
        required=True,
    )
    atributos.add_argument(
        "rewards_fk",
        type=int,
        required=True,
    )
    atributos.add_argument("active", type=bool, required=False, default=True),

    @rl_users_rewards.expect(atributos, validate=True)
    # @jwt_required()
    def post(self):
        dados = self.atributos.parse_args()
        date = datetime.now(timezone("America/Sao_Paulo"))
        dados["date"] = date

        relationship = rlUsersRewardsModel(**dados)
        try:
            relationship.save()

        except:
            return {"message": "Internal server error"}, 500

        return {
            "message": "rl_users_rewards created successfully",
            "rl_users_rewards": relationship.json(),
        }, 201  # Created


@rl_users_rewards.route("/alter/<int:rl_users_rewards_pk>")
class userAlter(Resource):

    atributos = reqparse.RequestParser()
    atributos.add_argument(
        "users_fk",
        type=int,
        required=True,
    )
    atributos.add_argument(
        "rewards_fk",
        type=int,
        required=True,
    )

    # @jwt_required()
    @rl_users_rewards.expect(atributos, validate=True)
    def put(self, rl_users_rewards_pk):
        user = rlUsersRewardsModel.find(rl_users_rewards_pk)
        if user:
            kwargs = self.atributos.parse_args()

            try:
                user.update(**kwargs)

                return {
                    "message": "user has been altered successfully.",
                    "data": user.json(),
                }, 200

            except:
                traceback.print_exc()
                return {"message": "Internal server error"}, 500

        return {"message": "user not found."}, 404


@rl_users_rewards.route("/list_rewards")
class listRewards(Resource):

    rl_users_rewards_model = rl_users_rewards.model(
        "Relationship Model",
        {
            "rewards_pk": fields.Integer(
                required=True, description="Figure id in data lake"
            ),
            "name": fields.String(
                required=True, max_length=145, description="Figure id in data lake"
            ),
            "date": fields.DateTime(required=True, description="Relationship key"),
            "picture_hash": fields.String(
                required=True, max_length=145, description="Figure id in data lake"
            ),
            "description": fields.String(
                required=True, max_length=250, description="Figure id in data lake"
            ),
        },
    )

    retorno_model = rl_users_rewards.model(
        "List Relationship Model",
        {
            "rewards": fields.List(fields.Nested(rl_users_rewards_model)),
        },
    )

    parser = rl_users_rewards.parser()
    parser.add_argument("users_fk", type=int, required=True)

    @rl_users_rewards.expect(parser)
    @rl_users_rewards.marshal_with(retorno_model)
    def get(self):

        CAMPOS = [
            "rewards_pk",
            "name",
            "date",
            "picture_hash",
            "description",
        ]

        dados = self.parser.parse_args()

        query = """SELECT
                    r.rewards_pk,
                    r.name,
                    reu.date,
                    r.picture_hash,
                    r.description
                FROM
                    rl_users_rewards reu
                LEFT JOIN rewards r ON
                    reu.rewards_fk = r.rewards_pk
                WHERE
                    reu.active = TRUE 
                    AND reu.users_fk = %s """

        query_params = []

        query_params.append(dados["users_fk"])

        conn = MySQLConnection()

        resultado = conn.execute(query, tuple(query_params))

        rewards = []
        if resultado:
            for linha in resultado:
                aux_dict = {}
                for chave, valor in zip(CAMPOS, linha):
                    aux_dict[chave] = valor
                rewards.append(aux_dict.copy())

        else:
            return {"message": "None country found with the required filters."}, 404

        retorno = {
            "rewards": rewards,
        }

        return marshal(retorno, self.retorno_model), 200


@rl_users_rewards.route("/<int:users_pk>/delete/")
class userDelete(Resource):

    @jwt_required()
    def delete(self, users_pk):
        try:
            user = rlUsersRewardsModel.find(users_pk)
            if user:
                rl_users_rewards.delete()
                return {"message": "user successfully deleted"}, 200
            return {"message": "user not found."}, 404
        except:
            return {"message": "Internal server error"}, 500
