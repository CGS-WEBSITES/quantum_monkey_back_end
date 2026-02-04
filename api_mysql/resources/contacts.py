from flask_restx import Namespace, Resource, fields
from models.contacts import ContactModel

contact = Namespace("Contacts", "Contact list (email only) endpoints")

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

        if ContactModel.find_by_email(email):
            contact.abort(400, "Email already exists")

        name = (data.get("name") or "").strip() or None
        ativo = data.get("ativo", True)

        new_contact = ContactModel(email=email, name=name, ativo=ativo)
        new_contact.save()
        return new_contact, 201


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
