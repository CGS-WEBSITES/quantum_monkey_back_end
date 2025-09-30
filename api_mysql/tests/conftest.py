import pytest
import os
import sys
from flask import Flask
from flask_restx import Api, Namespace, Resource, fields
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env de teste
test_env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(test_env_path):
    load_dotenv(test_env_path)

# Define variáveis de ambiente padrão se não existirem
os.environ.setdefault("PASSWORD", "test_password")
os.environ.setdefault("USER", "test_user")
os.environ.setdefault("HOST", "localhost")
os.environ.setdefault("DATABASE", "test_database")

# Cria instância SQLAlchemy independente para testes
banco = SQLAlchemy()

# ========================================
# MODELOS PARA TESTE (independentes)
# ========================================


class UserModel(banco.Model):
    __tablename__ = "users"

    users_pk = banco.Column(banco.Integer, primary_key=True)
    name = banco.Column(banco.String(145), nullable=False)
    email = banco.Column(banco.String(320), nullable=False, unique=True)

    def __init__(self, name, email):
        self.name = name
        self.email = email

    def json(self):
        return {
            "users_pk": self.users_pk,
            "name": self.name,
            "email": self.email,
        }

    @classmethod
    def find_user(cls, users_pk):
        return cls.query.filter_by(users_pk=users_pk).first()

    @classmethod
    def find_by_email(cls, email):
        return cls.query.filter_by(email=email).first()

    def save_user(self):
        banco.session.add(self)
        banco.session.commit()

    def delete_user(self):
        banco.session.delete(self)
        banco.session.commit()

    def update_user(self, **kwargs):
        for key, value in kwargs.items():
            if value is not None:
                setattr(self, key, value)
        self.save_user()


class ContactModel(banco.Model):
    __tablename__ = "contacts"

    contacts_pk = banco.Column(banco.Integer, primary_key=True)
    email = banco.Column(banco.String(320), nullable=False, unique=True, index=True)

    def __init__(self, email):
        self.email = (email or "").strip().lower()

    def json(self):
        return {
            "contacts_pk": self.contacts_pk,
            "email": self.email,
        }

    @classmethod
    def find(cls, contacts_pk):
        return cls.query.filter_by(contacts_pk=contacts_pk).first()

    @classmethod
    def find_by_email(cls, email):
        return cls.query.filter_by(email=(email or "").strip().lower()).first()

    def save(self):
        banco.session.add(self)
        banco.session.commit()

    def delete(self):
        banco.session.delete(self)
        banco.session.commit()

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if value is not None:
                if key == "email":
                    value = (value or "").strip().lower()
                setattr(self, key, value)
        self.save()


# ========================================
# RECURSOS/ENDPOINTS PARA TESTE (independentes)
# ========================================

# Namespace de usuários
user = Namespace("Users", "User related endpoints")
user_model = user.model(
    "User",
    {
        "users_pk": fields.Integer(readonly=True),
        "name": fields.String(required=True),
        "email": fields.String(required=True),
    },
)


@user.route("/")
class UserList(Resource):
    @user.marshal_list_with(user_model)
    def get(self):
        return UserModel.query.all()

    @user.expect(user_model)
    @user.marshal_with(user_model, code=201)
    def post(self):
        data = user.payload or {}

        # Validação de campos obrigatórios
        if not data.get("name"):
            user.abort(400, "Name is required")
        if not data.get("email"):
            user.abort(400, "Email is required")

        if UserModel.find_by_email(data["email"]):
            user.abort(400, "Email already exists")
        new_user = UserModel(name=data["name"], email=data["email"])
        new_user.save_user()
        return new_user, 201


@user.route("/<int:users_pk>")
class User(Resource):
    @user.marshal_with(user_model)
    def get(self, users_pk):
        user_obj = UserModel.find_user(users_pk)
        if not user_obj:
            user.abort(404, "User not found")
        return user_obj

    @user.expect(user_model)
    @user.marshal_with(user_model)
    def put(self, users_pk):
        user_obj = UserModel.find_user(users_pk)
        if not user_obj:
            user.abort(404, "User not found")
        data = user.payload
        if "email" in data and data["email"] != user_obj.email:
            if UserModel.find_by_email(data["email"]):
                user.abort(400, "Email already exists")
        user_obj.update_user(**data)
        return user_obj

    def delete(self, users_pk):
        user_obj = UserModel.find_user(users_pk)
        if not user_obj:
            user.abort(404, "User not found")
        user_obj.delete_user()
        return {"message": "User deleted successfully"}, 200


# Namespace de contatos
contact = Namespace("Contacts", "Contact list endpoints")
contact_model = contact.model(
    "Contact",
    {
        "contacts_pk": fields.Integer(readonly=True),
        "email": fields.String(required=True),
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
        new_contact = ContactModel(email=email)
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
            new_email = data["email"].strip().lower()
            if new_email != obj.email and ContactModel.find_by_email(new_email):
                contact.abort(400, "Email already exists")
            obj.update(email=new_email)
        return obj

    def delete(self, contacts_pk):
        obj = ContactModel.find(contacts_pk)
        if not obj:
            contact.abort(404, "Contact not found")
        obj.delete()
        return {"message": "Contact deleted successfully"}, 200


# ========================================
# FIXTURES DO PYTEST
# ========================================


@pytest.fixture(scope="session")
def app():
    """Cria uma instância da aplicação Flask para testes."""

    # Configuração para teste (SQLite em memória)
    app = Flask(__name__)
    app.config.update(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            "WTF_CSRF_ENABLED": False,
            "SECRET_KEY": "test-secret-key",
        }
    )

    # Inicializa o banco
    banco.init_app(app)

    # Cria a API
    api = Api(
        app,
        version="1.0",
        title="API de Testes",
        description="API para testes automatizados",
        doc="/docs/",
    )

    # Adiciona os namespaces
    api.add_namespace(user, "/users")
    api.add_namespace(contact, "/contacts")

    # Cria as tabelas
    with app.app_context():
        banco.create_all()

    yield app


@pytest.fixture
def client(app):
    """Cliente de teste Flask."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Runner para comandos CLI."""
    return app.test_cli_runner()


@pytest.fixture(autouse=True)
def clean_db(app):
    """Limpa o banco de dados antes de cada teste."""
    with app.app_context():
        banco.session.remove()
        banco.drop_all()
        banco.create_all()
