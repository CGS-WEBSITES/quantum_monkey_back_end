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

            # Upload spreadsheet to S3
            try:
                from resources.s3_images import get_s3_client, BUCKET_NAME
                s3_client = get_s3_client()
                s3_client.upload_fileobj(
                    Fileobj=BytesIO(raw),
                    Bucket=BUCKET_NAME,
                    Key=file.filename,
                    ExtraArgs={
                        "ContentType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    }
                )
                print(f"Uploaded {file.filename} to S3 bucket {BUCKET_NAME} successfully.")
            except Exception as s3_err:
                print(f"Error uploading file to S3: {s3_err}")

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

                # Fetch all contacts for name matching
                contacts = ContactModel.query.filter(ContactModel.name.isnot(None)).all()
                
                def normalize_name(n):
                    if not n:
                        return ""
                    import unicodedata
                    n = unicodedata.normalize('NFKD', n).encode('ASCII', 'ignore').decode('utf-8')
                    return " ".join(n.lower().split())

                contact_map = {}
                for c in contacts:
                    contact_map[normalize_name(c.name)] = c.email

                # Detect an "email" column dynamically in the first 5 rows
                email_col = None
                for row in root.findall('.//main:row', ns):
                    row_idx = int(row.get('r') or 0)
                    if row_idx > 5:
                        break
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
                        if val and isinstance(val, str):
                            val_clean = val.strip().lower()
                            if val_clean in ["email", "e-mail", "emails", "e-mails"]:
                                email_col = col
                                break
                    if email_col:
                        break

                # Get exchange rate from cell A1
                exchange_rate = 5.0  # default fallback
                for row in root.findall('.//main:row', ns):
                    row_idx = int(row.get('r') or 0)
                    if row_idx == 1:
                        for c in row.findall('main:c', ns):
                            cell_ref = c.get('r')
                            if get_col_letter(cell_ref) == 'A':
                                val_el = c.find('main:v', ns)
                                if val_el is not None:
                                    try:
                                        exchange_rate = float(val_el.text.strip().replace(',', '.'))
                                    except ValueError:
                                        pass
                                break
                        break

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

                    name = row_cells.get('A', '').strip()
                    if not name:
                        continue

                    # Skip header row or exchange rate row
                    if name.lower() in ["funcionário/sócio", "funcionario/socio", "name", "nome", "full name", "nome completo", "cotação", "cotacao"] or "cgs" in name.lower() or name.replace('.', '', 1).isdigit():
                        continue

                    # Skip if row doesn't have relevant values
                    if 'E' not in row_cells and 'K' not in row_cells:
                        continue

                    def to_float(v):
                        if not v:
                            return 0.0
                        try:
                            return float(str(v).replace(',', '.').strip())
                        except ValueError:
                            return 0.0

                    salary_brl = to_float(row_cells.get('E', '0'))
                    mei_brl = to_float(row_cells.get('F', '0'))
                    lunch_brl = to_float(row_cells.get('G', '0'))
                    extra_brl = to_float(row_cells.get('H', '0'))
                    lucro_brl = to_float(row_cells.get('I', '0'))
                    total_brl = to_float(row_cells.get('J', '0'))

                    # Get raw columns
                    salary_usd_val = to_float(row_cells.get('K', '0'))
                    profit_usd_val = to_float(row_cells.get('M', '0'))
                    total_usd_val = to_float(row_cells.get('R', '0'))  # Column R is the final paid amount

                    # If Column R is empty, fall back to Column O
                    if total_usd_val <= 0:
                        total_usd_val = to_float(row_cells.get('O', '0'))

                    # If Column O is also empty, fall back to sum of salary and profit
                    if total_usd_val <= 0:
                        total_usd_val = salary_usd_val + profit_usd_val

                    # If Column K (salary_usd) is empty, convert E (salary_brl)
                    if salary_usd_val <= 0 and salary_brl > 0 and exchange_rate > 0:
                        salary_usd_val = salary_brl / exchange_rate

                    # If Column M (profit_usd) is empty, convert I (lucro_brl)
                    if profit_usd_val <= 0 and lucro_brl > 0 and exchange_rate > 0:
                        profit_usd_val = lucro_brl / exchange_rate

                    # Get base reimbursement from BRL columns converted to USD
                    base_reimbursement_usd = 0.0
                    if exchange_rate > 0:
                        base_reimbursement_usd = (mei_brl + lunch_brl + extra_brl) / exchange_rate

                    calculo_final = salary_usd_val + base_reimbursement_usd + profit_usd_val
                    difference = total_usd_val - calculo_final

                    # Determine Wise fee and Diferença (Col P)
                    wise_fee = 0.0
                    diferenca_usd = 0.0

                    if difference > 0:
                        if difference <= 2.50:
                            wise_fee = difference
                            diferenca_usd = 0.0
                        elif 6.00 <= difference <= 8.00:
                            wise_fee = difference
                            diferenca_usd = 0.0
                        else:
                            wise_fee = 6.47
                            diferenca_usd = difference - wise_fee
                    else:
                        # Negative difference or zero difference
                        wise_fee = 0.0
                        diferenca_usd = difference

                    # Check if they have reimbursement (MEI or Lunch or Extra BRL)
                    has_reimbursement = (mei_brl > 0 or lunch_brl > 0 or extra_brl > 0)

                    if has_reimbursement:
                        extra_usd = base_reimbursement_usd + diferenca_usd
                        if extra_usd < 0:
                            extra_usd = 0.0
                        total_usd_val = salary_usd_val + extra_usd + profit_usd_val
                    else:
                        extra_usd = 0.0
                        # If no reimbursement, the difference goes to salary
                        salary_usd_val = salary_usd_val + diferenca_usd
                        total_usd_val = salary_usd_val + profit_usd_val

                    # Skip rows that are empty or totals row
                    if total_usd_val <= 0 and salary_usd_val <= 0 and salary_brl <= 0:
                        continue

                    email_source = None
                    email = ""
                    if email_col and row_cells.get(email_col):
                        email = str(row_cells.get(email_col)).strip()
                        if email:
                            email_source = "spreadsheet"

                    if not email:
                        email = contact_map.get(normalize_name(name), "")
                        if email:
                            email_source = "database"

                    invoices.append({
                        "name": name,
                        "email": email,
                        "email_source": email_source,
                        "salary_brl": salary_brl,
                        "mei_brl": mei_brl,
                        "lunch_brl": lunch_brl,
                        "other_benefits_brl": extra_brl,
                        "salary_usd": salary_usd_val,
                        "extra_usd": extra_usd,
                        "profit_usd": profit_usd_val,
                        "total_usd": total_usd_val
                    })

                return {"invoices": invoices}, 200

        except Exception as e:
            return {"message": f"Erro ao processar planilha: {str(e)}"}, 500


@sender.route("/send_invoice_single")
class SenderSendInvoiceSingle(Resource):
    def post(self):
        data = request.get_json(silent=True) or {}
        invoice = data.get("invoice")
        month_year = (data.get("month_year") or "").strip()
        due_date = (data.get("due_date") or "").strip()
        test_mode = bool(data.get("test_mode", True))
        sender_name = (data.get("sender_name") or "Bárbara Delmas").strip()
        sender_email = (data.get("sender_email") or "admin@wearecgs.com").strip()

        if not invoice:
            return {"message": "Campo 'invoice' é obrigatório."}, 400
        if not month_year:
            return {"message": "Mês/Ano 'month_year' é obrigatório."}, 400
        if not due_date:
            return {"message": "Data de vencimento 'due_date' é obrigatória."}, 400

        name = invoice.get("name")
        email = invoice.get("email")
        salary_usd = float(invoice.get("salary_usd", 0))
        extra_usd = float(invoice.get("extra_usd", 0))
        profit_usd = float(invoice.get("profit_usd", 0))
        total_usd = salary_usd + extra_usd + profit_usd

        # Subject
        subject = f"CGS ::: Confirmation of Payment Amount and Request for Invoice Submission Invoices Staff – {month_year}"

        # Construct dynamic payment text
        profit_text = ""
        if profit_usd > 0:
            profit_text = f" And more $ {profit_usd:.2f} USD for profit distribution."

        if extra_usd > 0:
            payment_text = f"According to our records, <strong>the total amount is $ {salary_usd:.2f} USD, plus a reimbursement for lunch and other associated costs totaling $ {extra_usd:.2f} USD.</strong>{profit_text}"
        else:
            payment_text = f"According to our records, <strong>the total amount is $ {salary_usd:.2f} USD.</strong>{profit_text}"

        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Invoice Confirmation</title>
            <style>
                body {{
                    font-family: Arial, Helvetica, sans-serif;
                    font-size: 14px;
                    line-height: 1.5;
                    color: #222222;
                }}
                p {{
                    margin: 0 0 16px 0;
                }}
                ol {{
                    margin: 0 0 16px 20px;
                    padding: 0;
                }}
                li {{
                    margin-bottom: 6px;
                }}
                a {{
                    color: #1155cc;
                    text-decoration: underline;
                }}
                .signature-table {{
                    margin-top: 30px;
                    border-top: 1px solid #e0e0e0;
                    padding-top: 20px;
                }}
            </style>
        </head>
        <body>
            <p>Dear {name},</p>
            
            <p>I trust this email finds you in good health. We want to express our sincere appreciation for the exceptional work you've been contributing as a valuable member of our team. Your dedication and commitment to our projects are highly regarded.</p>
            
            <p>We are reaching out to confirm the amount owed to you for the services you've provided. {payment_text}</p>
            
            <p>Please take a moment to review this amount and cross-check it with your records and do let us know if you find any discrepancies.</p>
            
            <p>To make the payment process smoother, we kindly request that you submit your invoice by {due_date}. To ensure a seamless and punctual payment, please include the following details in your invoice:</p>
            
            <ol>
                <li>Your full name or company name.</li>
                <li>Invoice dates.</li>
                <li>A comprehensive breakdown of services provided, including descriptions, quantities, and rates.</li>
                <li>Payment due date: {due_date}.</li>
            </ol>
            
            <p>You can send your invoice by replying to this email, addressing it to all relevant contacts (<a href="mailto:admin@wearecgs.com">admin@wearecgs.com</a>, <a href="mailto:marcio@wearecgs.com">marcio@wearecgs.com</a>, <a href="mailto:pmo@wearecgs.com">pmo@wearecgs.com</a>). If you have any questions or require further information, please don't hesitate to get in touch with our finance department at the previously mentioned email addresses.</p>
            
            <p>We fully understand the importance of timely payments and remain committed to ensuring that you receive your compensation promptly. Your cooperation in promptly submitting the invoice will greatly assist us in achieving this goal.</p>
            
            <p>Moreover, you have the option to generate your invoice directly through the Wise website using the following link: <a href="https://wise.com/us/invoice-generator" target="_blank">https://wise.com/us/invoice-generator</a>.</p>
            
            <p>If you need assistance with creating your invoice, please refer to the following link: <a href="https://www.notion.so/wearecgs/External-invoice-creation-wise-54053bda0fce420281a1accee381e549?pvs=4" target="_blank">https://www.notion.so/wearecgs/External-invoice-creation-wise-54053bda0fce420281a1accee381e549?pvs=4</a>.</p>
            
            <p>Once again, we want to express our gratitude for your unwavering dedication to our projects, and we eagerly anticipate the continuation of our successful collaboration.</p>
            
            <p>Thank you for your attention to this matter.</p>
            
            <p>Best regards,</p>
            
            <table class="signature-table" border="0" cellpadding="0" cellspacing="0">
                <tr>
                    <td style="padding-right: 15px; vertical-align: top;">
                        <img src="https://druna-assets.s3.us-east-2.amazonaws.com/cgs_logo.jpg" width="80" height="80" style="border-radius: 12px; object-fit: contain; border: 1px solid #e0e0e0; background: #ffffff; padding: 4px;" alt="CGS Logo">
                    </td>
                    <td style="font-family: Arial, sans-serif; font-size: 14px; line-height: 1.4; color: #333333; vertical-align: top;">
                        <strong style="color: #fb8c00; font-size: 16px;">{sender_name}</strong><br>
                        Finance & Operations Analyst<br>
                        CGS Group LLC<br>
                        Creative Games Studio | Games ForFun<br>
                        <br>
                        ✉️ <a href="mailto:admin@wearecgs.com">admin@wearecgs.com</a><br>
                        🌐 <a href="https://wearecgs.com">wearecgs.com</a><br>
                        🎮 Discord ID: barbaradelmas
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """

        body = html_template.format(
            name=name,
            payment_text=payment_text,
            due_date=due_date,
            sender_name=sender_name
        )

        recipient = "luiseduardoekenya7@gmail.com" if test_mode else email
        if not recipient:
            return {"message": "E-mail do destinatário não encontrado."}, 400

        try:
            resp = send(recipient, subject, body, sender=sender_email)
            if isinstance(resp, dict) and "error" in resp:
                return {"message": resp["error"]}, 500
            
            # Log single email in DB if we want, or just return success
            return {"message": "E-mail enviado com sucesso!"}, 200
        except Exception as e:
            return {"message": str(e)}, 500



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
                    <title>Invoice Confirmation</title>
                    <style>
                        body {{
                            font-family: Arial, Helvetica, sans-serif;
                            font-size: 14px;
                            line-height: 1.5;
                            color: #222222;
                        }}
                        p {{
                            margin: 0 0 16px 0;
                        }}
                        ol {{
                            margin: 0 0 16px 20px;
                            padding: 0;
                        }}
                        li {{
                            margin-bottom: 6px;
                        }}
                        a {{
                            color: #1155cc;
                            text-decoration: underline;
                        }}
                        .signature-table {{
                            margin-top: 30px;
                            border-top: 1px solid #e0e0e0;
                            padding-top: 20px;
                        }}
                    </style>
                </head>
                <body>
                    <p>Dear {name},</p>
                    
                    <p>I trust this email finds you in good health. We want to express our sincere appreciation for the exceptional work you've been contributing as a valuable member of our team. Your dedication and commitment to our projects are highly regarded.</p>
                    
                    <p>We are reaching out to confirm the amount owed to you for the services you've provided. {payment_text}</p>
                    
                    <p>Please take a moment to review this amount and cross-check it with your records and do let us know if you find any discrepancies.</p>
                    
                    <p>To make the payment process smoother, we kindly request that you submit your invoice by {due_date}. To ensure a seamless and punctual payment, please include the following details in your invoice:</p>
                    
                    <ol>
                        <li>Your full name or company name.</li>
                        <li>Invoice dates.</li>
                        <li>A comprehensive breakdown of services provided, including descriptions, quantities, and rates.</li>
                        <li>Payment due date: {due_date}.</li>
                    </ol>
                    
                    <p>You can send your invoice by replying to this email, addressing it to all relevant contacts (<a href="mailto:admin@wearecgs.com">admin@wearecgs.com</a>, <a href="mailto:marcio@wearecgs.com">marcio@wearecgs.com</a>, <a href="mailto:pmo@wearecgs.com">pmo@wearecgs.com</a>). If you have any questions or require further information, please don't hesitate to get in touch with our finance department at the previously mentioned email addresses.</p>
                    
                    <p>We fully understand the importance of timely payments and remain committed to ensuring that you receive your compensation promptly. Your cooperation in promptly submitting the invoice will greatly assist us in achieving this goal.</p>
                    
                    <p>Moreover, you have the option to generate your invoice directly through the Wise website using the following link: <a href="https://wise.com/us/invoice-generator" target="_blank">https://wise.com/us/invoice-generator</a>.</p>
                    
                    <p>If you need assistance with creating your invoice, please refer to the following link: <a href="https://www.notion.so/wearecgs/External-invoice-creation-wise-54053bda0fce420281a1accee381e549?pvs=4" target="_blank">https://www.notion.so/wearecgs/External-invoice-creation-wise-54053bda0fce420281a1accee381e549?pvs=4</a>.</p>
                    
                    <p>Once again, we want to express our gratitude for your unwavering dedication to our projects, and we eagerly anticipate the continuation of our successful collaboration.</p>
                    
                    <p>Thank you for your attention to this matter.</p>
                    
                    <p>Best regards,</p>
                    
                    <table class="signature-table" border="0" cellpadding="0" cellspacing="0">
                        <tr>
                            <td style="padding-right: 15px; vertical-align: top;">
                                <img src="https://druna-assets.s3.us-east-2.amazonaws.com/cgs_logo.jpg" width="80" height="80" style="border-radius: 12px; object-fit: contain; border: 1px solid #e0e0e0; background: #ffffff; padding: 4px;" alt="CGS Logo">
                            </td>
                            <td style="font-family: Arial, sans-serif; font-size: 14px; line-height: 1.4; color: #333333; vertical-align: top;">
                                <strong style="color: #fb8c00; font-size: 16px;">{sender_name}</strong><br>
                                Finance & Operations Analyst<br>
                                CGS Group LLC<br>
                                Creative Games Studio | Games ForFun<br>
                                <br>
                                ✉️ <a href="mailto:admin@wearecgs.com">admin@wearecgs.com</a><br>
                                🌐 <a href="https://wearecgs.com">wearecgs.com</a><br>
                                🎮 Discord ID: barbaradelmas
                            </td>
                        </tr>
                    </table>
                </body>
                </html>
                """

                for inv in inv_list:
                    name = inv.get("name")
                    email = inv.get("email")
                    salary_usd = float(inv.get("salary_usd", 0))
                    extra_usd = float(inv.get("extra_usd", 0))
                    profit_usd = float(inv.get("profit_usd", 0))
                    total_usd = salary_usd + extra_usd + profit_usd

                    # Subject
                    subject = f"CGS ::: Confirmation of Payment Amount and Request for Invoice Submission Invoices Staff – {m_y}"

                    # Construct dynamic payment text
                    profit_text = ""
                    if profit_usd > 0:
                        profit_text = f" And more $ {profit_usd:.2f} USD for profit distribution."

                    if extra_usd > 0:
                        payment_text = f"According to our records, <strong>the total amount is $ {salary_usd:.2f} USD, plus a reimbursement for lunch and other associated costs totaling $ {extra_usd:.2f} USD.</strong>{profit_text}"
                    else:
                        payment_text = f"According to our records, <strong>the total amount is $ {salary_usd:.2f} USD.</strong>{profit_text}"

                    # Body format
                    body = html_template.format(
                        name=name,
                        payment_text=payment_text,
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
