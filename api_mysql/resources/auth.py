from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models.users import UserModel

auth = Namespace("Auth", "Authentication endpoints")

# Modelos da API
register_model = auth.model(
    "Register",
    {
        "name": fields.String(required=True, description="Nome do usuário"),
        "email": fields.String(required=True, description="Email do usuário"),
        "password": fields.String(required=True, description="Senha do usuário (mínimo 6 caracteres)"),
    },
)

login_model = auth.model(
    "Login",
    {
        "email": fields.String(required=True, description="Email do usuário"),
        "password": fields.String(required=True, description="Senha do usuário"),
    },
)

token_response = auth.model(
    "TokenResponse",
    {
        "access_token": fields.String(description="JWT Access Token"),
        "user": fields.Raw(description="Dados do usuário"),
    },
)


@auth.route("/register")
class Register(Resource):
    @auth.expect(register_model)
    @auth.marshal_with(token_response, code=201)
    def post(self):
        """Registrar um novo usuário e retornar token JWT"""
        data = auth.payload

        # Validações
        if not data.get("name") or not data.get("email") or not data.get("password"):
            auth.abort(400, "Name, email and password are required")

        # Verificar se o email já existe
        if UserModel.find_by_email(data["email"]):
            auth.abort(400, "Email already exists")

        # Validar tamanho da senha
        if len(data["password"]) < 6:
            auth.abort(400, "Password must be at least 6 characters long")

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


@auth.route("/login")
class Login(Resource):
    @auth.expect(login_model)
    @auth.marshal_with(token_response)
    def post(self):
        """Fazer login e receber token JWT"""
        data = auth.payload

        # Validações
        if not data.get("email") or not data.get("password"):
            auth.abort(400, "Email and password are required")

        # Buscar usuário por email
        user = UserModel.find_by_email(data["email"])
        if not user:
            auth.abort(401, "Invalid email or password")

        # Verificar se está ativo
        if not user.ativo:
            auth.abort(403, "User account is inactive")

        # Verificar senha
        if not user.verify_password(data["password"]):
            auth.abort(401, "Invalid email or password")

        # Gerar token JWT
        access_token = create_access_token(identity=user.users_pk)

        return {
            "access_token": access_token,
            "user": user.json(),
        }


@auth.route("/me")
class Me(Resource):
    @jwt_required()
    @auth.doc(security="apikey")
    def get(self):
        """Obter informações do usuário autenticado"""
        current_user_id = get_jwt_identity()
        user = UserModel.find_user(current_user_id)

        if not user:
            auth.abort(404, "User not found")

        if not user.ativo:
            auth.abort(403, "User account is inactive")

        return user.json()