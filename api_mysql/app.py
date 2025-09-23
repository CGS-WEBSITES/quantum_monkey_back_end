# Imports do flask
from service_imports import *

from namespaces import add_namespaces

gunicorn_logger = logging.getLogger("gunicorn.error")

app = Flask(__name__)

# working solely with the flask logger
app.logger.handlers = gunicorn_logger.handlers
app.logger.setLevel(gunicorn_logger.level)

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# configs do JWT
app.config["JWT_TOKEN_LOCATION"] = ["headers", "cookies"]
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=12)

# configs de segurança extra (refresh tunado)
app.config["JWT_COOKIE_EXPIRES"] = timedelta(hours=8)


# VARIAVEIS DE AMBIENTE
app.config["JWT_SECRET_KEY"] = SECRET_KEY

bcrypt.init_app(app)

authorizations = {
    "apikey": {
        "type": "apiKey",
        "in": "header",
        "name": "Authorization",
        "description": "Type in the *'Value'* input box below: **'Bearer &lt;JWT&gt;'**, where JWT is the token",
    }
}

api = Api(
    app,
    title="API Drunagor Companion App",
    version="1.0",
    description="Api para implementação do Drunagor Companion App com Flask",
    authorizations=authorizations,
    security="apikey",
)

jwt = JWTManager(app)
cors = CORS(app, supports_credentials=True)
engine = create_engine(DATABASE_URI)

api = add_namespaces(api)

banco.init_app(app)

if __name__ == "__main__":

    with app.app_context():
        try:
            banco.create_all()
            print("Tabelas criadas com sucesso!")

        except Exception as e:
            print(f"conexão do banco: {DATABASE_URI}")
            print(f"Erro ao criar tabelas: {e}")

    app.run(host="0.0.0.0", debug=True, port="5000")
