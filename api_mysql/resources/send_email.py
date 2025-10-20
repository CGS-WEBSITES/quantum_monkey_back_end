from flask import request
from flask_restx import Resource, Namespace
import re

from email_sender import send
from models.contacts import ContactModel

sender = Namespace("Email Sender", description="Email related Endpoints")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _is_email(s: str) -> bool:
    return isinstance(s, str) and EMAIL_RE.match(s.strip()) is not None


@sender.route("/send_bulk")
class SenderSendBulk(Resource):
    def post(self):
        data = request.get_json(silent=True) or {}
        recipients = data.get("recipients") or []
        subject = (data.get("subject") or "").strip()
        html = data.get("htmlContent") or data.get("body") or ""

        if not isinstance(recipients, list) or not recipients:
            return {"message": "Campo 'recipients' deve ser uma lista não vazia."}, 400
        if not subject:
            return {"message": "Campo 'subject' é obrigatório."}, 400
        if not html:
            return {"message": "Campo 'htmlContent' (ou 'body') é obrigatório."}, 400

        clean_recipients = []
        for r in recipients:
            if isinstance(r, str):
                r = r.strip()
                if _is_email(r):
                    clean_recipients.append(r)

        if not clean_recipients:
            return {"message": "Nenhum e-mail válido em 'recipients'."}, 400

        print(f"Enviando emails para: {clean_recipients}")

        results = {"sent": [], "failed": []}

        for email in clean_recipients:
            try:
                resp = send(email, subject, html)

                if isinstance(resp, dict):
                    if "error" in resp:
                        error_msg = resp.get("error", "Erro desconhecido")
                        if "not authorized" in error_msg.lower():
                            error_msg += (
                                " (Verifique permissões IAM e identidade no SES)"
                            )

                        results["failed"].append({"email": email, "error": error_msg})
                    else:
                        results["sent"].append(email)

                elif isinstance(resp, tuple) and len(resp) == 2:
                    payload, status = resp
                    if status and int(status) >= 400:
                        error_msg = payload.get("error") or payload.get(
                            "message", "Erro no envio"
                        )

                        if "not authorized" in error_msg.lower():
                            error_msg += (
                                " (Verifique permissões IAM e identidade no SES)"
                            )
                        elif "not verified" in error_msg.lower():
                            error_msg += " (Email/domínio não verificado no SES)"

                        results["failed"].append({"email": email, "error": error_msg})
                    else:
                        results["sent"].append(email)
                else:
                    results["sent"].append(email)

            except Exception as e:
                error_msg = str(e)
                print(f"Erro ao enviar para {email}: {error_msg}")

                results["failed"].append({"email": email, "error": error_msg})

        print(
            f"Resultado: {len(results['sent'])} enviados, {len(results['failed'])} falharam"
        )

        response = {
            "message": "Envio em lote concluído",
            "requested_count": len(clean_recipients),
            "sent_count": len(results["sent"]),
            "failed_count": len(results["failed"]),
            "sent": results["sent"],
            "failed": results["failed"],
        }

        if len(results["sent"]) == 0 and len(results["failed"]) > 0:
            return response, 500  # Todas falharam
        else:
            return response, 200  # Sucesso total


@sender.route("/send_to_contacts")
class SenderSendToContacts(Resource):
    def post(self):
        data = request.get_json(silent=True) or {}
        subject = (data.get("subject") or "").strip()
        html = data.get("htmlContent") or data.get("body") or ""
        only_active = bool(data.get("only_active", True))
        ids = data.get("ids")

        if not subject:
            return {"message": "Campo 'subject' é obrigatório."}, 400
        if not html:
            return {"message": "Campo 'htmlContent' (ou 'body') é obrigatório."}, 400

        query = ContactModel.query
        if isinstance(ids, list) and ids:
            try:
                ids = [int(x) for x in ids]
                query = query.filter(ContactModel.contacts_pk.in_(ids))
            except Exception:
                return {"message": "Campo 'ids' deve ser uma lista de inteiros."}, 400

        if only_active:
            query = query.filter_by(ativo=True)

        contacts = query.order_by(ContactModel.contacts_pk.asc()).all()
        if not contacts:
            return {"message": "Nenhum contato encontrado para envio."}, 404

        results = {"sent": [], "failed": []}
        for c in contacts:
            if not _is_email(c.email):
                results["failed"].append({"email": c.email, "error": "E-mail inválido"})
                continue
            try:
                resp = send(c.email, subject, html)
                if isinstance(resp, tuple) and len(resp) == 2:
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
                    results["sent"].append(c.email)
            except Exception as e:
                results["failed"].append({"email": c.email, "error": str(e)})

        return {
            "message": "Broadcast concluído",
            "total_contacts": len(contacts),
            "sent_count": len(results["sent"]),
            "failed_count": len(results["failed"]),
            "sent": results["sent"],
            "failed": results["failed"],
        }, 200
