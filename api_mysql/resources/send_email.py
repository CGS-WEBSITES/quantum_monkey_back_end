from flask import request
from flask_restx import Resource, Namespace
import re

from email_sender import send
from models.contacts import ContactModel

sender = Namespace("Email Sender", description="Email related Endpoints")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _is_email(s: str) -> bool:
    return isinstance(s, str) and EMAIL_RE.match(s.strip()) is not None


def _extract_error_message(resp):
    if isinstance(resp, dict):
        return resp.get("error") or resp.get("message", "Erro desconhecido")
    elif isinstance(resp, tuple) and len(resp) >= 1:
        payload = resp[0]
        if isinstance(payload, dict):
            return payload.get("error") or payload.get("message", "Erro desconhecido")
    return str(resp)


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
        invalid_emails = []
        for r in recipients:
            if isinstance(r, str):
                r = r.strip().lower()
                if _is_email(r):
                    clean_recipients.append(r)
                else:
                    invalid_emails.append(r)

        if not clean_recipients:
            return {
                "message": "Nenhum e-mail válido em 'recipients'.",
                "invalid_emails": invalid_emails[:10],
            }, 400

        print(
            f"[Email Sender] Iniciando envio para {len(clean_recipients)} destinatários"
        )

        results = {"sent": [], "failed": []}

        for email in clean_recipients:
            try:
                resp = send(email, subject, html)

                if isinstance(resp, dict):
                    if "error" in resp:
                        error_msg = _extract_error_message(resp)
                        results["failed"].append({"email": email, "error": error_msg})
                        print(
                            f"[Email Sender] Falha ao enviar para {email}: {error_msg}"
                        )
                    else:
                        results["sent"].append(email)
                        print(f"[Email Sender] Enviado com sucesso para {email}")

                elif isinstance(resp, tuple) and len(resp) == 2:
                    payload, status = resp
                    if status and int(status) >= 400:
                        error_msg = _extract_error_message(payload)
                        results["failed"].append({"email": email, "error": error_msg})
                        print(
                            f"[Email Sender] Falha ao enviar para {email}: {error_msg}"
                        )
                    else:
                        results["sent"].append(email)
                        print(f"[Email Sender] Enviado com sucesso para {email}")
                else:
                    results["sent"].append(email)
                    print(f"[Email Sender] Enviado com sucesso para {email}")

            except Exception as e:
                error_msg = str(e)
                print(f"[Email Sender] Exceção ao enviar para {email}: {error_msg}")
                results["failed"].append({"email": email, "error": error_msg})

        print(
            f"[Email Sender] Resultado: {len(results['sent'])} enviados, {len(results['failed'])} falharam"
        )

        response = {
            "message": "Envio em lote concluído",
            "requested_count": len(clean_recipients),
            "sent_count": len(results["sent"]),
            "failed_count": len(results["failed"]),
            "sent": results["sent"],
            "failed": results["failed"],
        }

        if invalid_emails:
            response["invalid_emails"] = invalid_emails[:10]

        if len(results["sent"]) == 0 and len(results["failed"]) > 0:
            return response, 500
        elif len(results["failed"]) > 0:
            return response, 207
        else:
            return response, 200


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
            except (ValueError, TypeError):
                return {"message": "Campo 'ids' deve ser uma lista de inteiros."}, 400

        if only_active:
            query = query.filter_by(ativo=True)

        contacts = query.order_by(ContactModel.contacts_pk.asc()).all()

        if not contacts:
            return {"message": "Nenhum contato encontrado para envio."}, 404

        print(f"[Email Sender] Enviando para {len(contacts)} contatos")

        results = {"sent": [], "failed": []}

        for contact in contacts:
            email = contact.email

            if not _is_email(email):
                results["failed"].append({"email": email, "error": "E-mail inválido"})
                continue

            try:
                resp = send(email, subject, html)

                if isinstance(resp, tuple) and len(resp) == 2:
                    payload, status = resp
                    if status and int(status) >= 400:
                        error_msg = _extract_error_message(payload)
                        results["failed"].append({"email": email, "error": error_msg})
                    else:
                        results["sent"].append(email)
                elif isinstance(resp, dict) and "error" in resp:
                    error_msg = _extract_error_message(resp)
                    results["failed"].append({"email": email, "error": error_msg})
                else:
                    results["sent"].append(email)

            except Exception as e:
                results["failed"].append({"email": email, "error": str(e)})

        print(
            f"[Email Sender] Broadcast: {len(results['sent'])} enviados, {len(results['failed'])} falharam"
        )

        response = {
            "message": "Broadcast concluído",
            "total_contacts": len(contacts),
            "sent_count": len(results["sent"]),
            "failed_count": len(results["failed"]),
            "sent": results["sent"],
            "failed": results["failed"],
        }

        if len(results["sent"]) == 0 and len(results["failed"]) > 0:
            return response, 500
        elif len(results["failed"]) > 0:
            return response, 207
        else:
            return response, 200


@sender.route("/test")
class SenderTest(Resource):
    def post(self):
        """
        Endpoint de teste para verificar configuração do SES.

        Body JSON:
        {
            "email": "test@example.com"
        }
        """
        data = request.get_json(silent=True) or {}
        email = (data.get("email") or "").strip()

        if not _is_email(email):
            return {"message": "Email inválido"}, 400

        subject = "Teste de Configuração - Email Marketing"
        html = """
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h1 style="color: #4CAF50;">✅ Teste de Email</h1>
                <p>Se você está recebendo este email, a configuração do SES está funcionando corretamente!</p>
                <hr>
                <p style="color: #666; font-size: 12px;">
                    Este é um email de teste enviado pelo sistema de Email Marketing.
                </p>
            </body>
            </html>
        """

        try:
            resp = send(email, subject, html)

            if isinstance(resp, dict) and "error" in resp:
                return {
                    "success": False,
                    "message": f"Erro ao enviar: {resp['error']}",
                }, 500
            elif isinstance(resp, tuple) and len(resp) == 2:
                payload, status = resp
                if status and int(status) >= 400:
                    return {
                        "success": False,
                        "message": f"Erro ao enviar: {_extract_error_message(payload)}",
                    }, 500

            return {
                "success": True,
                "message": f"Email de teste enviado com sucesso para {email}",
            }, 200

        except Exception as e:
            return {"success": False, "message": f"Exceção ao enviar: {str(e)}"}, 500
