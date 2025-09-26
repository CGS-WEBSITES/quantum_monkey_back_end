from flask_restx import Resource, Namespace, reqparse
from flask_jwt_extended import jwt_required
from email_sender import send


sender = Namespace("Email Sender", "Email related Endpoints")


@sender.route("/send")
class senderSend(Resource):

    atributos = reqparse.RequestParser()
    atributos.add_argument("recipient", type=str, required=True)
    atributos.add_argument("subject", type=str, required=True)
    atributos.add_argument("body", type=str, required=True)

    @sender.expect(atributos, validate=True)
    @jwt_required()
    def post(self):
        dados = self.atributos.parse_args()

        return send(dados["recipient"], dados["subject"], dados["body"])
