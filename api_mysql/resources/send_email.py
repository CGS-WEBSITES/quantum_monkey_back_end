from flask import request
from flask_restx import Resource, Namespace
import re
import zipfile
import xml.etree.ElementTree as ET
from io import BytesIO
from werkzeug.datastructures import FileStorage

from email_sender import send
from models.contacts import ContactModel
from models.email_logs import EmailLogModel

sender = Namespace("Email Sender", description="Email related Endpoints")


@sender.route("/history")
class SenderHistory(Resource):
    def get(self):
        logs = EmailLogModel.query.order_by(EmailLogModel.id.desc()).limit(50).all()
        return [log.json() for log in logs], 200

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

        # Create log entry
        log_entry = EmailLogModel(
            subject=subject,
            recipient_count=len(clean_recipients),
            status="Sending"
        )
        log_entry.save()

        import threading
        from flask import current_app
        app = current_app._get_current_object()

        def bg_send_bulk(recipients_list, email_subject, email_html, log_id):
            with app.app_context():
                sent_count = 0
                failed_count = 0
                for email in recipients_list:
                    try:
                        resp = send(email, email_subject, email_html)
                        if isinstance(resp, dict) and "error" in resp:
                            failed_count += 1
                        else:
                            sent_count += 1
                    except Exception:
                        failed_count += 1
                
                log = EmailLogModel.query.get(log_id)
                if log:
                    log.update(
                        status="Completed" if failed_count == 0 else ("Failed" if sent_count == 0 else "Partial"),
                        sent_count=sent_count,
                        failed_count=failed_count
                    )

        # Start background thread
        threading.Thread(
            target=bg_send_bulk,
            args=(clean_recipients, subject, html, log_entry.id),
            daemon=True
        ).start()

        response = {
            "message": "Envio em lote iniciado em segundo plano.",
            "requested_count": len(clean_recipients),
            "sent_count": len(clean_recipients),
            "failed_count": 0,
            "sent": clean_recipients,
            "failed": [],
        }

        if invalid_emails:
            response["invalid_emails"] = invalid_emails[:10]

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

        email_list = []
        invalid_emails = []
        for contact in contacts:
            email = (contact.email or "").strip().lower()
            if _is_email(email):
                email_list.append(email)
            else:
                invalid_emails.append(email)

        # Create log entry
        log_entry = EmailLogModel(
            subject=subject,
            recipient_count=len(email_list),
            status="Sending"
        )
        log_entry.save()

        import threading
        from flask import current_app
        app = current_app._get_current_object()

        def bg_send_contacts(recipients_list, email_subject, email_html, log_id):
            with app.app_context():
                sent_count = 0
                failed_count = 0
                for email in recipients_list:
                    try:
                        resp = send(email, email_subject, email_html)
                        if isinstance(resp, dict) and "error" in resp:
                            failed_count += 1
                        else:
                            sent_count += 1
                    except Exception:
                        failed_count += 1
                
                log = EmailLogModel.query.get(log_id)
                if log:
                    log.update(
                        status="Completed" if failed_count == 0 else ("Failed" if sent_count == 0 else "Partial"),
                        sent_count=sent_count,
                        failed_count=failed_count
                    )

        # Start background thread
        threading.Thread(
            target=bg_send_contacts,
            args=(email_list, subject, html, log_entry.id),
            daemon=True
        ).start()

        response = {
            "message": "Broadcast iniciado em segundo plano.",
            "total_contacts": len(contacts),
            "sent_count": len(email_list),
            "failed_count": 0,
            "sent": email_list,
            "failed": [],
        }

        if invalid_emails:
            response["invalid_emails"] = invalid_emails[:10]

        return response, 200


excel_parser = sender.parser()
excel_parser.add_argument(
    "file",
    type=FileStorage,
    location="files",
    required=True,
    help="Excel file containing invoices (.xlsx)",
)


@sender.route("/parse_invoices")
class SenderParseInvoices(Resource):
    @sender.expect(excel_parser)
    def post(self):
        args = excel_parser.parse_args()
        file = args["file"]
        if not file:
            return {"message": "Nenhum arquivo fornecido."}, 400

        try:
            raw = file.read()
            if not raw:
                return {"message": "Arquivo vazio."}, 400
            file_stream = BytesIO(raw)

            # Parse Excel using standard zipfile + ElementTree
            ns = {
                'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
            }

            with zipfile.ZipFile(file_stream, 'r') as z:
                # Load shared strings
                shared_strings = []
                try:
                    sst_data = z.read('xl/sharedStrings.xml')
                    root = ET.fromstring(sst_data)
                    for si in root.findall('main:si', ns):
                        t = si.find('main:t', ns)
                        if t is not None:
                            shared_strings.append(t.text or "")
                        else:
                            r_texts = []
                            for r in si.findall('main:r', ns):
                                rt = r.find('main:t', ns)
                                if rt is not None and rt.text:
                                    r_texts.append(rt.text)
                            shared_strings.append("".join(r_texts))
                except KeyError:
                    pass

                # Load sheet1
                sheet_data = z.read('xl/worksheets/sheet1.xml')
                root = ET.fromstring(sheet_data)

                def get_col_letter(cell_ref):
                    return "".join([c for c in cell_ref if c.isalpha()])

                invoices = []
                for row in root.findall('.//main:row', ns):
                    row_cells = {}
                    for c in row.findall('main:c', ns):
                        cell_ref = c.get('r')
                        col = get_col_letter(cell_ref)
                        cell_type = c.get('t')
                        val_el = c.find('main:v', ns)
                        val = ""
                        if val_el is not None:
                            val = val_el.text
                            if cell_type == 's':
                                idx = int(val)
                                if 0 <= idx < len(shared_strings):
                                    val = shared_strings[idx]
                                else:
                                    val = ""
                        row_cells[col] = val.strip() if isinstance(val, str) else val

                    name = row_cells.get('A', '')
                    email = row_cells.get('B', '')

                    if not name or not email or '@' not in email:
                        continue

                    # Skip header row if name looks like a header
                    if name.lower() in ["name", "nome", "full name", "nome completo"]:
                        continue

                    def to_float(v):
                        if not v:
                            return 0.0
                        try:
                            return float(str(v).replace(',', '.'))
                        except ValueError:
                            return 0.0

                    salary = to_float(row_cells.get('C', '0'))
                    mei = to_float(row_cells.get('D', '0'))
                    lunch = to_float(row_cells.get('E', '0'))
                    other = to_float(row_cells.get('F', '0'))

                    invoices.append({
                        "name": name,
                        "email": email,
                        "salary_brl": salary,
                        "mei_brl": mei,
                        "lunch_brl": lunch,
                        "other_benefits_brl": other
                    })

                return {"invoices": invoices}, 200

        except Exception as e:
            return {"message": f"Erro ao processar planilha: {str(e)}"}, 500


@sender.route("/send_invoices")
class SenderSendInvoices(Resource):
    def post(self):
        data = request.get_json(silent=True) or {}
        invoices = data.get("invoices") or []
        month_year = (data.get("month_year") or "").strip()
        due_date = (data.get("due_date") or "").strip()
        test_mode = bool(data.get("test_mode", True))
        sender_name = (data.get("sender_name") or "Bárbara Delmas").strip()
        sender_email = (data.get("sender_email") or "admin@wearecgs.com").strip()

        if not invoices:
            return {"message": "Lista de faturas 'invoices' é obrigatória."}, 400
        if not month_year:
            return {"message": "Mês/Ano 'month_year' é obrigatório."}, 400
        if not due_date:
            return {"message": "Data de vencimento 'due_date' é obrigatória."}, 400

        # Log entry
        subject_template = f"CGS ::: Confirmation of Payment Amount and Request for Invoice Submission Invoices Staff – {month_year}"
        log_entry = EmailLogModel(
            subject=subject_template,
            recipient_count=len(invoices),
            status="Sending"
        )
        log_entry.save()

        import threading
        from flask import current_app
        app = current_app._get_current_object()

        def bg_send_invoices(inv_list, m_y, d_d, is_test, s_name, s_email, log_id):
            with app.app_context():
                sent_count = 0
                failed_count = 0

                html_template = """
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <title>Invoice Request</title>
                    <style>
                        body {{
                            font-family: Arial, sans-serif;
                            background-color: #f4f4f4;
                            color: #333333;
                            margin: 0;
                            padding: 20px;
                        }}
                        .container {{
                            background-color: #ffffff;
                            max-width: 600px;
                            margin: 0 auto;
                            padding: 30px;
                            border-radius: 8px;
                            border: 1px solid #dddddd;
                            box-shadow: 0 4px 8px rgba(0,0,0,0.05);
                        }}
                        h2 {{
                            color: #2c585c;
                            border-bottom: 2px solid #26d980;
                            padding-bottom: 10px;
                        }}
                        .value-box {{
                            background-color: #f0f7f4;
                            border-left: 4px solid #26d980;
                            padding: 15px;
                            margin: 20px 0;
                            border-radius: 0 4px 4px 0;
                        }}
                        .value-box p {{
                            margin: 5px 0;
                            font-size: 16px;
                        }}
                        .footer {{
                            margin-top: 30px;
                            border-top: 1px solid #eeeeee;
                            padding-top: 20px;
                            font-size: 14px;
                            color: #777777;
                        }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h2>CGS - Invoice Confirmation</h2>
                        <p>Dear {name},</p>
                        <p>I trust this email finds you in good health. We want to express our sincere appreciation for the exceptional work you've been contributing as a valuable member of our team. Your dedication and commitment to our projects are highly regarded.</p>
                        
                        <p>We are reaching out to confirm the amount owed to you for the services you've provided. According to our records, the details are as follows:</p>
                        
                        <div class="value-box">
                            <p><strong>Service Value:</strong> $ {salary_usd:.2f} USD</p>
                            <p><strong>Reimbursement (Lunch, MEI & other costs):</strong> $ {extra_usd:.2f} USD</p>
                            <p><strong>Total Amount:</strong> $ {total_usd:.2f} USD</p>
                        </div>
                        
                        <p>Please take a moment to review this amount and cross-check it with your records and do let us know if you find any discrepancies.</p>
                        
                        <p>To make the payment process smoother, we kindly request that you submit your invoice by <strong>{due_date}</strong>. To ensure a seamless and punctual payment, please include the following details in your invoice:</p>
                        
                        <ol>
                            <li>Your full name or company name.</li>
                            <li>Invoice dates.</li>
                            <li>A comprehensive breakdown of services provided, including descriptions, quantities, and rates.</li>
                            <li>Payment due date: <strong>{due_date}</strong>.</li>
                        </ol>
                        
                        <p>You can send your invoice by replying to this email, addressing it to all relevant contacts (<a href="mailto:admin@wearecgs.com">admin@wearecgs.com</a>, <a href="mailto:marcio@wearecgs.com">marcio@wearecgs.com</a>, <a href="mailto:pmo@wearecgs.com">pmo@wearecgs.com</a>).</p>
                        
                        <p>Moreover, you have the option to generate your invoice directly through the Wise website using the following link: <a href="https://wise.com/us/invoice-generator" target="_blank">https://wise.com/us/invoice-generator</a>.</p>
                        
                        <p>If you need assistance with creating your invoice, please refer to the following link: <a href="https://www.notion.so/wearecgs/External-invoice-creation-wise-54053bda0fce420281a1accee381e549?pvs=4" target="_blank">CGS Notion Guide</a>.</p>
                        
                        <p>Once again, we want to express our gratitude for your unwavering dedication to our projects, and we eagerly anticipate the continuation of our successful collaboration.</p>
                        
                        <p>Thank you for your attention to this matter.</p>
                        
                        <div class="footer">
                            <p>Best regards,</p>
                            <p><strong>{sender_name}</strong><br>
                            Finance & Operations Analyst<br>
                            CGS Group LLC | Creative Games Studio</p>
                        </div>
                    </div>
                </body>
                </html>
                """

                for inv in inv_list:
                    name = inv.get("name")
                    email = inv.get("email")
                    salary_usd = float(inv.get("salary_usd", 0))
                    extra_usd = float(inv.get("extra_usd", 0))
                    total_usd = salary_usd + extra_usd

                    # Subject
                    subject = f"CGS ::: Confirmation of Payment Amount and Request for Invoice Submission Invoices Staff – {m_y}"

                    # Body format
                    body = html_template.format(
                        name=name,
                        salary_usd=salary_usd,
                        extra_usd=extra_usd,
                        total_usd=total_usd,
                        due_date=d_d,
                        sender_name=s_name
                    )

                    recipient = "luiseduardoekenya7@gmail.com" if is_test else email

                    try:
                        resp = send(recipient, subject, body, sender=s_email)
                        if isinstance(resp, dict) and "error" in resp:
                            failed_count += 1
                        else:
                            sent_count += 1
                    except Exception:
                        failed_count += 1

                # Update log status
                log = EmailLogModel.query.get(log_id)
                if log:
                    log.update(
                        status="Completed" if failed_count == 0 else ("Failed" if sent_count == 0 else "Partial"),
                        sent_count=sent_count,
                        failed_count=failed_count
                    )

        # Start thread
        threading.Thread(
            target=bg_send_invoices,
            args=(invoices, month_year, due_date, test_mode, sender_name, sender_email, log_entry.id),
            daemon=True
        ).start()

        return {
            "message": "Envio de faturas iniciado em segundo plano.",
            "requested_count": len(invoices),
            "test_mode": test_mode,
            "log_id": log_entry.id
        }, 200
