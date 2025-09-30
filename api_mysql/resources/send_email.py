from flask_restx import Resource, Namespace, reqparse, inputs
from flask_jwt_extended import jwt_required
from email_sender import send
from models.contacts import ContactModel

sender = Namespace("Email Sender", "Email related Endpoints")


@sender.route("/send")
class senderSend(Resource):
    atributos = reqparse.RequestParser()
    atributos.add_argument("recipient", type=str, required=True, location="args")
    atributos.add_argument("subject", type=str, required=True, location="args")
    atributos.add_argument("body", type=str, required=True, location="args")

    @sender.expect(atributos, validate=True)
    @jwt_required()
    def post(self):
        dados = self.atributos.parse_args()
        return send(dados["recipient"], dados["subject"], dados["body"])


@sender.route("/send_to_contacts")
class SenderSendToContacts(Resource):
    args = reqparse.RequestParser()
    args.add_argument("subject", type=str, required=True, location="args")
    args.add_argument("body", type=str, required=True, location="args")
    args.add_argument("only_active", type=inputs.boolean, default=True, location="args")
    args.add_argument(
        "ids",
        type=str,
        required=False,
        location="args",
        help="Lista de contacts_pk separados por vírgula (ex: 1,2,3)",
    )

    @sender.expect(args, validate=True)
    @jwt_required()
    def post(self):
        data = self.args.parse_args()
        subject = (data.get("subject") or "").strip()
        body = data.get("body") or ""
        only_active = bool(data.get("only_active"))
        ids_param = (data.get("ids") or "").strip()

        # Monta a query base
        query = ContactModel.query
        if ids_param:
            try:
                id_list = [int(x) for x in ids_param.split(",") if x.strip().isdigit()]
                if id_list:
                    query = query.filter(ContactModel.contacts_pk.in_(id_list))
            except ValueError:
                sender.abort(
                    400,
                    "Invalid 'ids' parameter. Use only comma-separated numbers.",
                )
        if only_active:
            query = query.filter_by(ativo=True)

        contacts = query.order_by(ContactModel.contacts_pk.asc()).all()
        if not contacts:
            sender.abort(404, "Nenhum contato encontrado para envio.")

        results = {"sent": [], "failed": []}

        for c in contacts:
            resp = send(c.email, subject, body)
            # 'send' pode retornar (payload, status) em erro
            if isinstance(resp, tuple):
                payload, status = resp
                if status and int(status) >= 400:
                    results["failed"].append(
                        {
                            "email": c.email,
                            "error": payload.get("error") or payload.get("message"),
                        }
                    )
                else:
                    results["sent"].append(c.email)
            else:
                # sucesso
                results["sent"].append(c.email)

        return {
            "message": "Broadcast concluído",
            "total_contacts": len(contacts),
            "sent_count": len(results["sent"]),
            "failed_count": len(results["failed"]),
            "sent": results["sent"],
            "failed": results["failed"],
        }, 200
