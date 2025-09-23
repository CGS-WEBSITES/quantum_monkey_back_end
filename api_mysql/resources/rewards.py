import traceback
from flask_restx import Resource, Namespace, reqparse, fields, marshal
from models.rewards import RewardsModel
from flask_jwt_extended import jwt_required
from sql_alchemy import MySQLConnection
from math import ceil
from utils import boolean_string


reward = Namespace("Rewards", "Rewards related Endpoints")


@reward.route("/cadastro")
class RewardsRegister(Resource):

    atributos = reqparse.RequestParser()
    atributos.add_argument(
        "name",
        type=str,
        required=True,
    ),
    atributos.add_argument(
        "picture_hash",
        type=str,
        required=True,
    ),
    atributos.add_argument(
        "description",
        type=str,
        required=True,
    ),
    atributos.add_argument("active", type=bool, required=False, default=True),

    @reward.expect(atributos, validate=True)
    @jwt_required()
    def post(self):
        dados = self.atributos.parse_args()

        if RewardsModel.find_by_name(dados["name"]):
            return (
                {"message": "The reward '{}' already exists.".format(dados["name"])},
                400,
            )

        reward = RewardsModel(**dados)
        try:
            reward.save()

        except:
            reward.remove()
            traceback.print_exc()
            return {"message": "Internal server error"}, 500

        return {
            "message": "reward created successfully",
            "user": reward.json(),
        }, 201  # Created


@reward.route("/search")
class RewardsSearch(Resource):
    reward_model = reward.model(
        "Rewards Model",
        {
            "rewards_pk": fields.Integer(required=True, description="reward key"),
            "name": fields.String(
                required=True, max_length=145, description="reward name"
            ),
            "picture_hash": fields.String(
                required=True, max_length=250, description="reward name"
            ),
            "description": fields.String(
                required=True, max_length=145, description="reward name"
            ),
        },
    )

    retorno_model = reward.model(
        "Search reward Model",
        {
            "rewards": fields.List(fields.Nested(reward_model)),
            "current_page": fields.Integer,
            "last_page": fields.Integer,
        },
    )

    parser = reward.parser()
    parser.add_argument("active", type=boolean_string, required=False, default=True)
    parser.add_argument("limit", type=int, required=False, default=30)
    parser.add_argument("offset", type=int, required=False, default=0)

    @jwt_required()
    @reward.expect(parser)
    @reward.marshal_with(retorno_model)
    def get(self):
        CAMPOS = [
            "rewards_pk",
            "name",
            "picture_hash",
            "description",
        ]

        dados = self.parser.parse_args()

        query = """SELECT
                        S.rewards_pk,
                        S.name,
                        S.picture_hash,
                        S.description
                    FROM
                        rewards S
                    WHERE
                        S.active = %s"""

        query_params = []

        query_params.append(dados["active"])

        conn = MySQLConnection()
        resultado = conn.execute(query, tuple(query_params))

        contagem = "SELECT COUNT(*) FROM (" + query + ") as users_contagem;"
        ocorrencias = conn.execute(contagem, tuple(query_params))[0][0]
        pagina_atual = int(dados["offset"] / dados["limit"]) + 1
        ultima_pagina = ceil(ocorrencias / dados["limit"])

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
            "current_page": pagina_atual,
            "last_page": ultima_pagina,
        }

        return marshal(retorno, self.retorno_model), 200


@reward.route("/<int:rewards_pk>")
class rewardGet(Resource):

    @jwt_required()
    def get(self, rewards_pk):
        reward = RewardsModel.find(rewards_pk)

        if reward:
            return reward.json(), 200

        return {"message": "reward not found."}, 404  # not found


@reward.route("/<int:rewards_pk>/delete/")
class rewardDelete(Resource):

    @jwt_required()
    def delete(self, rewards_pk):
        try:
            reward = RewardsModel.find(rewards_pk)
            if reward:
                reward.delete()
                return {"message": "reward successfully deleted"}, 200
            return {"message": "reward not found."}, 404
        except:
            return {"message": "Internal server error"}, 500
