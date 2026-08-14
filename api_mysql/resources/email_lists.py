from flask import request
from flask_restx import Namespace, Resource, fields
from models.email_lists import EmailListModel
from flask_jwt_extended import jwt_required

email_list_ns = Namespace("Lists", "Email list management endpoints")

list_model = email_list_ns.model(
    "EmailList",
    {
        "id": fields.Integer(readonly=True),
        "name": fields.String(required=True),
        "description": fields.String(required=False),
        "slug": fields.String(readonly=True),
        "ativo": fields.Boolean(required=False, default=True),
        "contacts_count": fields.Integer(readonly=True),
        "total_contacts": fields.Integer(readonly=True),
    },
)


@email_list_ns.route("/")
class EmailListCollection(Resource):
    @jwt_required(optional=True)
    def get(self):
        # Garantir que existe ao menos a lista padrão 'Marketing'
        EmailListModel.get_or_create_default()
        lists = EmailListModel.query.filter_by(ativo=True).order_by(EmailListModel.id.asc()).all()
        return [l.json() for l in lists], 200

    @jwt_required(optional=True)
    @email_list_ns.expect(list_model, validate=True)
    def post(self):

        data = request.get_json(silent=True) or {}
        name = (data.get("name") or "").strip()
        if not name:
            return {"message": "Campo 'name' é obrigatório"}, 400

        description = (data.get("description") or "").strip() or None

        slug = name.lower().replace(" ", "-")
        existing = EmailListModel.find_by_slug(slug)
        if existing:
            if not existing.ativo:
                existing.update(name=name, description=description, ativo=True)
                return existing.json(), 200
            return {"message": f"Já existe uma lista com o nome '{name}'"}, 400

        new_list = EmailListModel(name=name, description=description, slug=slug, ativo=True)
        new_list.save()
        return new_list.json(), 201


@email_list_ns.route("/<int:list_id>")
class EmailListResource(Resource):
    @jwt_required()
    def get(self, list_id):
        obj = EmailListModel.find_by_id(list_id)
        if not obj or not obj.ativo:
            return {"message": "Lista não encontrada"}, 404
        return obj.json(), 200

    @jwt_required()
    @email_list_ns.expect(list_model)
    def put(self, list_id):
        obj = EmailListModel.find_by_id(list_id)
        if not obj or not obj.ativo:
            return {"message": "Lista não encontrada"}, 404

        data = request.get_json(silent=True) or {}
        if "name" in data:
            name = (data["name"] or "").strip()
            if not name:
                return {"message": "Campo 'name' não pode ser vazio"}, 400
            obj.update(name=name)

        if "description" in data:
            description = (data["description"] or "").strip() or None
            obj.update(description=description)

        return obj.json(), 200

    @jwt_required()
    def delete(self, list_id):
        obj = EmailListModel.find_by_id(list_id)
        if not obj:
            return {"message": "Lista não encontrada"}, 404
        
        # Não permitir deletar a lista padrão ID 1 se for a única
        if list_id == 1:
            total_active = EmailListModel.query.filter_by(ativo=True).count()
            if total_active <= 1:
                return {"message": "Não é possível excluir a lista padrão de Marketing"}, 400

        obj.delete()
        return {"message": "Lista desativada com sucesso"}, 200
