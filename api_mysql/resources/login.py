from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models.users import UserModel

# Namespace de login
login = Namespace("Login", "Login and authentication endpoints")

# Modelos da API
create_login_model = login.model(
    "CreateLogin",
    {
        "name": fields.String(required=True, description="Nome do usuário"),
        "email": fields.String(required=True, description="Email do usuário"),
        "password": fields.String(
            required=True, description="Senha do usuário (mínimo 6 caracteres)"
        ),
    },
)

login_model = login.model(
    "Login",
    {
        "email": fields.String(required=True, description="Email do usuário"),
        "password": fields.String(required=True, description="Senha do usuário"),
    },
)

token_response = login.model(
    "TokenResponse",
    {
        "access_token": fields.String(description="JWT Access Token"),
        "user": fields.Raw(description="Dados do usuário"),
    },
)


@login.route("/create")
class CreateLogin(Resource):
    @login.expect(create_login_model)
    @login.marshal_with(token_response, code=201)
    def post(self):
        """Criar um novo login (cadastro de usuário)"""
        data = login.payload

        # Validações
        if not data.get("name") or not data.get("email") or not data.get("password"):
            login.abort(400, "Name, email and password are required")

        # Verificar se o email já existe
        if UserModel.find_by_email(data["email"]):
            login.abort(400, "Email already exists")

        # Validar tamanho da senha
        if len(data["password"]) < 6:
            login.abort(400, "Password must be at least 6 characters long")

        # Criar novo usuário
        new_user = UserModel(
            name=data["name"],
            email=data["email"],
            password=data["password"],
            ativo=True,
        )
        new_user.save_user()

        # Gerar token JWT
        access_token = create_access_token(identity=new_user.users_pk)

        return {
            "access_token": access_token,
            "user": new_user.json(),
        }, 201


@login.route("/")
class Login(Resource):
    @login.expect(login_model)
    @login.marshal_with(token_response)
    def post(self):
        """Fazer login e receber token JWT"""
        data = login.payload

        # Validações
        if not data.get("email") or not data.get("password"):
            login.abort(400, "Email and password are required")

        # Buscar usuário por email
        user = UserModel.find_by_email(data["email"])
        if not user:
            login.abort(401, "Invalid email or password")

        # Verificar se está ativo
        if not user.ativo:
            login.abort(403, "User account is inactive")

        # Verificar senha
        if not user.verify_password(data["password"]):
            login.abort(401, "Invalid email or password")

        # Gerar token JWT
        access_token = create_access_token(identity=user.users_pk)

        return {
            "access_token": access_token,
            "user": user.json(),
        }


@login.route("/me")
class Me(Resource):
    @jwt_required()
    @login.doc(security="apikey")
    def get(self):
        """Obter informações do usuário autenticado"""
        current_user_id = get_jwt_identity()
        user = UserModel.find_user(current_user_id)

        if not user:
            login.abort(404, "User not found")

        if not user.ativo:
            login.abort(403, "User account is inactive")

        return user.json()
