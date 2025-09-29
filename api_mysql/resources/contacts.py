from flask_restx import Namespace, Resource, fields
from models.contacts import ContactModel

# Namespace da feature de contatos (somente e-mail)
contact = Namespace("Contacts", "Contact list (email only) endpoints")

# Modelo de serialização/validação do contato
contact_model = contact.model(
    "Contact",
    {
        "contacts_pk": fields.Integer(readonly=True),  # PK só leitura
        "email": fields.String(required=True),  # e-mail obrigatório
    },
)


@contact.route("/")
class ContactList(Resource):
    # GET /Contacts/ -> lista todos os contatos
    @contact.marshal_list_with(contact_model)
    def get(self):
        return ContactModel.query.order_by(
          ContactModel.contacts_pk.desc()).all()

    # POST /Contacts/ -> cria um novo contato
    @contact.expect(contact_model, validate=True)
    @contact.marshal_with(contact_model, code=201)
    def post(self):
        data = contact.payload or {}
        email = (data.get("email") or "").strip().lower()
        if not email:
            contact.abort(400, "Email is required")

        if ContactModel.find_by_email(email):
            contact.abort(400, "Email already exists")

        new_contact = ContactModel(email=email)
        new_contact.save()
        return new_contact, 201


@contact.route("/<int:contacts_pk>")
class Contact(Resource):
    # GET /Contacts/<id> -> busca contato específico
    @contact.marshal_with(contact_model)
    def get(self, contacts_pk):
        obj = ContactModel.find(contacts_pk)
        if not obj:
            contact.abort(404, "Contact not found")
        return obj

    # PUT /Contacts/<id> -> atualiza e-mail
    @contact.expect(contact_model)
    @contact.marshal_with(contact_model)
    def put(self, contacts_pk):
        obj = ContactModel.find(contacts_pk)
        if not obj:
            contact.abort(404, "Contact not found")

        data = contact.payload or {}
        if "email" in data and data["email"] is not None:
            new_email = data["email"].strip().lower()
            if new_email != obj.email and ContactModel.find_by_email(
              new_email
            ):
                contact.abort(400, "Email already exists")
            obj.update(email=new_email)

        return obj

    # DELETE /Contacts/<id> -> remove contato
    def delete(self, contacts_pk):
        obj = ContactModel.find(contacts_pk)
        if not obj:
            contact.abort(404, "Contact not found")
        obj.delete()
        return {"message": "Contact deleted successfully"}, 200
