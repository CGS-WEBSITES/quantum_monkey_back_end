from flask_restx import Namespace, Resource, fields
from models.users import UserModel

# Namespace da feature de usuários (define o prefixo e a descrição)
user = Namespace("Users", "User related endpoints")

# Modelo de serialização/validação do usuário (entra/saí da API)
user_model = user.model(
    "User",
    {
        "users_pk": fields.Integer(readonly=True),  # PK só leitura
        "name": fields.String(required=True),  # nome obrigatório
        "email": fields.String(required=True),  # email obrigatório
        "ativo": fields.Boolean(required=False, default=True),  # default True
    },
)


@user.route("/")
class UserList(Resource):
    # GET /Users/ -> listo todos os usuários
    @user.marshal_list_with(user_model)
    def get(self):
        return UserModel.query.all()

    # POST /Users/ -> crio um novo usuário
    @user.expect(user_model)  # espero payload conforme o modelo
    @user.marshal_with(user_model, code=201)  # retorno o usuário criado
    def post(self):
        data = user.payload or {}
        # se o email já existir, impeço duplicidade
        if "email" not in data or "name" not in data:
            user.abort(400, "Field 'name' and 'email' are required")

        if UserModel.find_by_email(data["email"]):
            user.abort(400, "Email already exists")

        # pega ativo do payload (se vier), senão True
        ativo = data.get("ativo", True)

        # crio e salvo o novo registro
        new_user = UserModel(name=data["name"], email=data["email"], ativo=ativo)
        new_user.save_user()
        return new_user, 201


@user.route("/<int:users_pk>")
class User(Resource):
    # GET /Users/<id> -> busco um usuário específico
    @user.marshal_with(user_model)
    def get(self, users_pk):
        user_obj = UserModel.find_user(users_pk)
        if not user_obj:
            user.abort(404, "User not found")  # retorno 404 se não existir
        return user_obj

    # PUT /Users/<id> -> atualizo um usuário existente
    @user.expect(user_model)  # recebo os campos do modelo
    @user.marshal_with(user_model)  # devolvo o usuário atualizado
    def put(self, users_pk):
        user_obj = UserModel.find_user(users_pk)
        if not user_obj:
            user.abort(404, "User not found")

        data = user.payload or {}

        # se email mudou, valido duplicidade antes de atualizar
        if "email" in data and data["email"] != user_obj.email:
            if UserModel.find_by_email(data["email"]):
                user.abort(400, "Email already exists")

        # atualizo só o que veio preenchido
        user_obj.update_user(**data)
        return user_obj

    # DELETE /Users/<id> -> removo o usuário
    def delete(self, users_pk):
        user_obj = UserModel.find_user(users_pk)
        if not user_obj:
            user.abort(404, "User not found")

        user_obj.delete_user()
        return {"message": "User deleted successfully"}, 200
