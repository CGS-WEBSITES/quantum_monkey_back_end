from flask import request
from flask_restx import Namespace, Resource, fields
import re
from models.contacts import ContactModel

contact = Namespace("Contacts", "Contact list (email only) endpoints")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _is_email(s: str) -> bool:
    return isinstance(s, str) and EMAIL_RE.match(s.strip()) is not None

contact_model = contact.model(
    "Contact",
    {
        "contacts_pk": fields.Integer(readonly=True),
        "email": fields.String(required=True),
        "name": fields.String(required=False),
        "ativo": fields.Boolean(required=False, default=True),
    },
)


@contact.route("/")
class ContactList(Resource):
    @contact.marshal_list_with(contact_model)
    def get(self):
        return ContactModel.query.order_by(ContactModel.contacts_pk.desc()).all()

    @contact.expect(contact_model, validate=True)
    @contact.marshal_with(contact_model, code=201)
    def post(self):
        data = contact.payload or {}

        email = (data.get("email") or "").strip().lower()
        if not email:
            contact.abort(400, "Email is required")

        name = (data.get("name") or "").strip() or None
        ativo = data.get("ativo", True)

        existing_contact = ContactModel.find_by_email(email)
        if existing_contact:
            existing_contact.update(ativo=True, name=name or existing_contact.name)
            return existing_contact, 201

        new_contact = ContactModel(email=email, name=name, ativo=ativo)
        new_contact.save()
        return new_contact, 201


@contact.route("/bulk")
class ContactBulkList(Resource):
    def post(self):
        from sql_alchemy import banco
        data = request.get_json(silent=True) or {}
        contacts_list = data.get("contacts") or []

        if not isinstance(contacts_list, list) or not contacts_list:
            return {"message": "Campo 'contacts' deve ser uma lista não vazia."}, 400

        added_count = 0
        updated_count = 0

        for item in contacts_list:
            email = (item.get("email") or "").strip().lower()
            if not email or not _is_email(email):
                continue

            name = (item.get("name") or "").strip() or None

            existing = ContactModel.find_by_email(email)
            if existing:
                existing.update(ativo=True, name=name or existing.name)
                updated_count += 1
            else:
                new_contact = ContactModel(email=email, name=name, ativo=True)
                banco.session.add(new_contact)
                added_count += 1

        banco.session.commit()
        return {
            "message": "Importação em lote concluída",
            "added": added_count,
            "updated": updated_count
        }, 201


@contact.route("/subscribe")
class ContactSubscribePage(Resource):
    def get(self):
        from flask import make_response

        html_content = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Subscribe - Creative Games Studio</title>
            <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700;900&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
            <style>
                * {
                    box-sizing: border-box;
                }
                body {
                    margin: 0;
                    padding: 0;
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-family: 'Inter', sans-serif;
                    color: #ffffff;
                    background-image: url('https://druna-assets.s3.us-east-2.amazonaws.com/Newsletter.png');
                    background-size: cover;
                    background-position: center;
                    background-repeat: no-repeat;
                    background-attachment: fixed;
                    background-color: #0c0c0e;
                }
                @media (max-width: 767px) {
                    body {
                        background-image: url('https://druna-assets.s3.us-east-2.amazonaws.com/NewsletterMobile.png');
                    }
                }
                .overlay {
                    position: absolute;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(12, 12, 14, 0.60);
                    z-index: 1;
                }
                .container {
                    position: relative;
                    z-index: 2;
                    width: 100%;
                    max-width: 420px;
                    padding: 16px;
                }
                .card {
                    background: #141416;
                    border: 1px solid #282830;
                    border-radius: 16px;
                    padding: 40px 32px;
                    box-shadow: 0 15px 35px rgba(0, 0, 0, 0.8);
                    text-align: center;
                }
                .logo-container {
                    margin-bottom: 24px;
                }
                .logo-img {
                    height: 80px;
                    width: 80px;
                    border-radius: 12px;
                    object-fit: contain;
                    border: 1px solid #282830;
                    background: #ffffff;
                    padding: 4px;
                }
                h1 {
                    font-family: 'Outfit', sans-serif;
                    font-size: 24px;
                    font-weight: 800;
                    text-transform: uppercase;
                    letter-spacing: 0.08em;
                    margin: 0 0 10px 0;
                    color: #ffffff;
                }
                p.subtitle {
                    font-size: 13px;
                    color: #a0a0ab;
                    line-height: 1.5;
                    margin: 0 0 28px 0;
                    font-weight: 400;
                }
                .form-group {
                    text-align: left;
                    margin-bottom: 20px;
                }
                label {
                    display: block;
                    font-size: 10px;
                    color: #8e8e9f;
                    margin-bottom: 6px;
                    font-weight: 700;
                    text-transform: uppercase;
                    letter-spacing: 0.08em;
                }
                input[type="text"], input[type="email"] {
                    width: 100%;
                    padding: 14px 16px;
                    background: #1c1c1f;
                    border: 1px solid #2d2d34;
                    border-radius: 8px;
                    color: #ffffff;
                    font-size: 14px;
                    font-family: 'Inter', sans-serif;
                    transition: all 0.2s ease;
                }
                input[type="text"]:focus, input[type="email"]:focus {
                    outline: none;
                    border-color: #26d980;
                    background: #222226;
                }
                .checkbox-container {
                    display: flex;
                    align-items: flex-start;
                    text-align: left;
                    margin-bottom: 28px;
                    cursor: pointer;
                    user-select: none;
                }
                .checkbox-container input {
                    margin-top: 2px;
                    margin-right: 10px;
                    accent-color: #26d980;
                    width: 14px;
                    height: 14px;
                }
                .checkbox-text {
                    font-size: 11px;
                    color: #8e8e9f;
                    line-height: 1.4;
                }
                .btn {
                    width: 100%;
                    padding: 16px;
                    background: #26d980;
                    color: #0d0d0e;
                    border: none;
                    border-radius: 8px;
                    font-family: 'Outfit', sans-serif;
                    font-size: 14px;
                    font-weight: 700;
                    text-transform: uppercase;
                    letter-spacing: 0.08em;
                    cursor: pointer;
                    transition: all 0.2s ease;
                }
                .btn:hover:not(:disabled) {
                    background: #34e48c;
                    box-shadow: 0 4px 12px rgba(38, 217, 128, 0.2);
                }
                .btn:disabled {
                    opacity: 0.4;
                    cursor: not-allowed;
                }
                .success-view {
                    display: none;
                }
                .success-icon-container {
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    width: 64px;
                    height: 64px;
                    background: rgba(38, 217, 128, 0.1);
                    border: 1px solid rgba(38, 217, 128, 0.3);
                    border-radius: 50%;
                    margin-bottom: 20px;
                }
                .success-icon {
                    color: #26d980;
                    font-size: 28px;
                    font-weight: bold;
                }
                .success-title {
                    font-family: 'Outfit', sans-serif;
                    font-size: 24px;
                    font-weight: 800;
                    margin: 0 0 10px 0;
                    text-transform: uppercase;
                    letter-spacing: 0.08em;
                }
                .motto {
                    font-size: 10px;
                    color: #52525b;
                    font-style: italic;
                    margin-top: 28px;
                    letter-spacing: 0.08em;
                    text-transform: uppercase;
                    font-weight: 600;
                }
            </style>
            <script>
                async function submitForm(event) {
                    event.preventDefault();
                    const btn = document.getElementById('submitBtn');
                    const email = document.getElementById('email').value.trim();
                    const name = document.getElementById('name').value.trim();

                    if (!email) return;

                    btn.disabled = true;
                    btn.innerText = 'Subscribing...';

                    try {
                        const response = await fetch('/qmonkey/contacts/', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ email, name: name || null, ativo: true })
                        });

                        if (response.ok) {
                            document.getElementById('formView').style.display = 'none';
                            document.getElementById('successView').style.display = 'block';
                            document.getElementById('successEmail').innerText = email;
                        } else {
                            const errData = await response.json();
                            alert(errData.message || 'Error subscribing. Please try again.');
                            btn.disabled = false;
                            btn.innerText = 'Subscribe';
                        }
                    } catch (e) {
                        alert('Network error. Please try again.');
                        btn.disabled = false;
                        btn.innerText = 'Subscribe';
                    }
                }
            </script>
        </head>
        <body>
            <div class="overlay"></div>
            <div class="container">
                <div class="card" id="formView">
                    <div class="logo-container">
                        <img class="logo-img" src="https://druna-assets.s3.us-east-2.amazonaws.com/cgs_logo.jpg" alt="Creative Games Studio">
                    </div>
                    <h1>Newsletter</h1>
                    <p class="subtitle">Join our community to receive launch alerts, campaign milestones, and exclusive rewards.</p>

                    <form onsubmit="submitForm(event)">
                        <div class="form-group">
                            <label for="name">Your Name</label>
                            <input type="text" id="name" placeholder="Enter your name" autocomplete="name">
                        </div>
                        <div class="form-group">
                            <label for="email">Email Address</label>
                            <input type="email" id="email" required placeholder="Enter your email address" autocomplete="email">
                        </div>

                        <label class="checkbox-container">
                            <input type="checkbox" required checked>
                            <span class="checkbox-text">
                                I agree to receive newsletters, updates, and special marketing communications from Creative Games Studio.
                            </span>
                        </label>

                        <button type="submit" class="btn" id="submitBtn">Subscribe</button>
                    </form>
                </div>

                <div class="card success-view" id="successView">
                    <div class="success-icon-container">
                        <span class="success-icon">&#10004;</span>
                    </div>
                    <h1 class="success-title">Thank You!</h1>
                    <p class="subtitle">Your email <strong id="successEmail" style="color: #26d980;"></strong> has been added to our list. Welcome to the adventure.</p>
                    <div class="motto">We build worlds. You make them yours.</div>
                </div>
            </div>
        </body>
        </html>
        """

        return make_response(html_content, 200)


@contact.route("/unsubscribe")
class ContactUnsubscribe(Resource):
    def get(self):
        from flask import request, make_response
        email = request.args.get("email")
        if not email:
            return make_response(
                "<html><body><div style='text-align: center; margin-top: 50px; font-family: sans-serif;'>"
                "<h2>Email is required</h2>"
                "</div></body></html>", 400
            )

        email = email.strip().lower()
        obj = ContactModel.find_by_email(email)
        if not obj:
            return make_response(
                "<html><body><div style='text-align: center; margin-top: 50px; font-family: sans-serif;'>"
                "<h2>Subscription Cancelled / Inscrição Cancelada</h2>"
                "<p>O e-mail <b>" + email + "</b> não está cadastrado ou já foi desinscrito.</p>"
                "<p>The email address <b>" + email + "</b> is not registered or has already been unsubscribed.</p>"
                "</div></body></html>", 200
            )

        obj.update(ativo=False)
        return make_response(
            "<html><body><div style='text-align: center; margin-top: 50px; font-family: sans-serif;'>"
            "<h2>Desinscrição Realizada com Sucesso / Unsubscribed Successfully</h2>"
            "<p>Seu e-mail <b>" + email + "</b> foi removido da nossa newsletter e você não receberá novos e-mails.</p>"
            "<p>Your email <b>" + email + "</b> has been removed from our newsletter list.</p>"
            "</div></body></html>", 200
        )


@contact.route("/<int:contacts_pk>")
class Contact(Resource):
    @contact.marshal_with(contact_model)
    def get(self, contacts_pk):
        obj = ContactModel.find(contacts_pk)
        if not obj:
            contact.abort(404, "Contact not found")
        return obj

    @contact.expect(contact_model)
    @contact.marshal_with(contact_model)
    def put(self, contacts_pk):
        obj = ContactModel.find(contacts_pk)
        if not obj:
            contact.abort(404, "Contact not found")

        data = contact.payload or {}

        if "email" in data and data["email"] is not None:
            new_email = (data["email"] or "").strip().lower()
            if new_email != obj.email and ContactModel.find_by_email(new_email):
                contact.abort(400, "Email already exists")
            obj.update(email=new_email)

        if "name" in data and data["name"] is not None:
            new_name = (data["name"] or "").strip() or None
            obj.update(name=new_name)

        if "ativo" in data and data["ativo"] is not None:
            obj.update(ativo=bool(data["ativo"]))

        return obj

    def delete(self, contacts_pk):
        obj = ContactModel.find(contacts_pk)
        if not obj:
            contact.abort(404, "Contact not found")
        obj.delete()
        return {"message": "Contact deleted successfully"}, 200
