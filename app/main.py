import os
from flask import Flask
from dotenv import load_dotenv
from flask_restx import Api

from .extensions import db, bcrypt

def create_app():
    load_dotenv()
    app = Flask(__name__)

    db_user = os.environ.get('MYSQL_USER')
    db_password = os.environ.get('MYSQL_PASSWORD')
    db_name = os.environ.get('MYSQL_DATABASE')
    db_host = 'db' 

    app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    api = Api(app,
              version='1.0',
              title='Email Sender API',
              description='Uma API para envio de emails e gerenciamento de usuários.')

    db.init_app(app)
    bcrypt.init_app(app)

    from .resources.auth import auth_ns
    
    api.add_namespace(auth_ns, path='/auth')

    with app.app_context():
        db.create_all()
            
    return app

# O bloco if __name__ == '__main__' continua o mesmo
if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)