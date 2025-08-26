import os
from flask import Flask, jsonify, request
from dotenv import load_dotenv

from extensions import db, bcrypt
from models import UserModel

def create_app():
    load_dotenv()
    app = Flask(__name__)

    db_user = os.environ.get('MYSQL_USER')
    db_password = os.environ.get('MYSQL_PASSWORD')
    db_name = os.environ.get('MYSQL_DATABASE')
    db_host = 'db' 

    app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+mysqlconnector://{db_user}:{db_password}@{db_host}/{db_name}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    bcrypt.init_app(app)

    with app.app_context():
        db.create_all()

    @app.route('/')
    def index():
        return jsonify({"status": "API is running!"})

    @app.route('/register', methods=['POST'])
    def register():
        data = request.get_json()

        if not data or not data.get('username') or not data.get('password') or not data.get('email'):
            return jsonify({"message": "Faltando username, email ou password"}), 400

        if UserModel.find_by_username(data['username']):
            return jsonify({"message": "Um usuário com esse nome já existe"}), 400
        if UserModel.find_by_email(data['email']):
            return jsonify({"message": "Um usuário com esse email já existe"}), 400

        new_user = UserModel(
            username=data['username'],
            email=data['email'],
            password=data['password']
        )

        try:
            new_user.save_to_db()
            return jsonify({"message": "Usuário criado com sucesso."}), 201
        except Exception as e:
            print(e)
            return jsonify({"message": "Ocorreu um erro ao criar o usuário."}), 500
            
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)