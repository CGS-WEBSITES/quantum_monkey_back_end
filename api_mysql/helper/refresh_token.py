from datetime import datetime, timedelta
from pytz import timezone
from blacklist import BLACKLIST
from flask_restx import Resource, Namespace, fields, abort
from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity,
    get_jwt,
    create_access_token,
)

refresh = Namespace("Refresh token", "Rota para atualizar o token prestes a vencer")


@refresh.route("refresh")
class Refreshing(Resource):
    @jwt_required(refresh=True)
    def post(self):
        try:
            exp_timestamp = get_jwt()["exp"]
            now = datetime.now(timezone("America/Sao_Paulo"))
            target_timestamp = datetime.timestamp(now + timedelta(minutes=3))
            if target_timestamp > exp_timestamp:
                access_token = create_access_token(identity=get_jwt_identity())
                return {"access_token": access_token}, 200
            else:
                abort(400, message="Token válido, ainda.")
        except KeyError:
            return {"message": "Chave inválida"}, 500
