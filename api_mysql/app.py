# Imports do flask
from service_imports import *
from flask_cors import CORS
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

# Configurações adicionais para upload
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # Limite de 16MB para uploads
app.config["RESTX_MASK_SWAGGER"] = False  # Desabilita masking no Swagger
app.config["ERROR_404_HELP"] = False  # Remove ajuda automática em 404

bcrypt.init_app(app)

# CONFIGURAÇÃO MELHORADA DO CORS - ISSO RESOLVE O PROBLEMA!
cors = CORS(
    app,
    resources={
        r"/*": {
            "origins": [
                "http://localhost:5004",
                "http://localhost:5000",
                "http://localhost:3000",
                "http://127.0.0.1:5004",
                "http://127.0.0.1:5000",
                "*",  # Em produção, remova este e deixe apenas as origens específicas
            ],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
            "allow_headers": [
                "Content-Type",
                "Authorization",
                "X-Requested-With",
                "Accept",
                "Origin",
                "Access-Control-Request-Method",
                "Access-Control-Request-Headers",
            ],
            "expose_headers": ["Content-Range", "X-Content-Range"],
            "supports_credentials": True,
            "send_wildcard": False,
            "max_age": 3600,
        }
    },
)

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
    doc="/docs",  # URL do Swagger UI
)

jwt = JWTManager(app)
engine = create_engine(DATABASE_URI)

# Adiciona os namespaces incluindo o de assets
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
