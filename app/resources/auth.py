from flask import request
from flask_restx import Namespace, Resource
from models import UserModel

auth_ns = Namespace('auth', description='Operações de Autenticação')

@auth_ns.route('/register')
class Register(Resource):
    def post(self):
        data = request.get_json()

        if not data or not data.get('username') or not data.get('password') or not data.get('email'):
            return {"message": "Faltando username, email ou password"}, 400

        if UserModel.find_by_username(data['username']):
            return {"message": "Um usuário com esse nome já existe"}, 400
        if UserModel.find_by_email(data['email']):
            return {"message": "Um usuário com esse email já existe"}, 400

        new_user = UserModel(
            username=data['username'],
            email=data['email'],
            password=data['password']
        )

        try:
            new_user.save_to_db()
            return {"message": "Usuário criado com sucesso."}, 201
        except Exception as e:
            print(e)
            return {"message": "Ocorreu um erro ao criar o usuário."}, 500