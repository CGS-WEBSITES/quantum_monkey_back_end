import traceback
from flask_restx import Resource, Namespace, reqparse, fields, marshal
from models.rl_events_rewards import rlEventsRewardsModel
from flask_jwt_extended import jwt_required
from sql_alchemy import MySQLConnection

rl_events_rewards = Namespace(
    "Event Rewards Relationship", "Events relationships related Endpoints"
)


@rl_events_rewards.route("/cadastro")
class eventRegister(Resource):

    atributos = reqparse.RequestParser()
    atributos.add_argument(
        "events_fk",
        type=int,
        required=True,
    )
    atributos.add_argument(
        "rewards_fk",
        type=int,
        required=True,
    )
    atributos.add_argument("active", type=bool, required=False, default=True),

    @rl_events_rewards.expect(atributos, validate=True)
    @jwt_required()
    def post(self):
        dados = self.atributos.parse_args()

        relationship = rlEventsRewardsModel(**dados)
        try:
            relationship.save()

        except:
            return {"message": "Internal server error"}, 500

        return {
            "message": "rl_events_rewards created successfully",
            "rl_events_rewards": relationship.json(),
        }, 201  # Created


@rl_events_rewards.route("/alter/<int:rl_events_rewards_pk>")
class eventAlter(Resource):

    atributos = reqparse.RequestParser()
    atributos.add_argument(
        "events_fk",
        type=int,
        required=True,
    )
    atributos.add_argument(
        "rewards_fk",
        type=int,
        required=True,
    )

    @jwt_required()
    @rl_events_rewards.expect(atributos, validate=True)
    def put(self, rl_events_rewards_pk):
        event = rlEventsRewardsModel.find(rl_events_rewards_pk)
        if event:
            kwargs = self.atributos.parse_args()

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


@rl_events_rewards.route("/list_rewards")
class listRewards(Resource):

    rl_events_rewards_model = rl_events_rewards.model(
        "Relationship Model",
        {
            "rewards_pk": fields.Integer(
                required=True, description="Figure id in data lake"
            ),
            "name": fields.String(
                required=True, max_length=145, description="Figure id in data lake"
            ),
            "description": fields.String(
                required=True, max_length=250, description="Figure id in data lake"
            ),
            "picture_hash": fields.String(
                required=True, max_length=145, description="Figure id in data lake"
            ),
        },
    )

    retorno_model = rl_events_rewards.model(
        "List Relationship Model",
        {
            "rewards": fields.List(fields.Nested(rl_events_rewards_model)),
        },
    )

    parser = rl_events_rewards.parser()
    parser.add_argument("events_fk", type=int, required=True)

    @rl_events_rewards.expect(parser)
    @rl_events_rewards.marshal_with(retorno_model)
    def get(self):

        CAMPOS = [
            "rewards_pk",
            "name",
            "picture_hash",
            "description",
        ]

        dados = self.parser.parse_args()

        query = """SELECT
                    r.rewards_pk,
                    r.name,
                    r.picture_hash,
                    r.description
                FROM
                    rl_events_rewards reu
                LEFT JOIN rewards r ON
                    reu.rewards_fk = r.rewards_pk
                WHERE
                    reu.active = TRUE 
                    AND reu.events_fk = %s """

        query_params = []

        query_params.append(dados["events_fk"])

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


@rl_events_rewards.route("/<int:events_pk>/delete/")
class eventDelete(Resource):

    @jwt_required()
    def delete(self, events_pk):
        try:
            event = rlEventsRewardsModel.find(events_pk)
            if event:
                rl_events_rewards.delete()
                return {"message": "event successfully deleted"}, 200
            return {"message": "event not found."}, 404
        except:
            return {"message": "Internal server error"}, 500
