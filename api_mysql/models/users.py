from sql_alchemy import banco
from sqlalchemy import Boolean, text


# Modelo da tabela de usuários
class UserModel(banco.Model):
    __tablename__ = "users"

    # PK do usuário
    users_pk = banco.Column(banco.Integer, primary_key=True)
    # Nome do usuário (obrigatório)
    name = banco.Column(banco.String(145), nullable=False)
    # Email único do usuário (obrigatório)
    email = banco.Column(banco.String(320), nullable=False, unique=True)
    # Indica se o usuário está ativo (default True)
    # server_default garante o default no banco; default garante no ORM
    ativo = banco.Column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("1"),  # MySQL/MariaDB: usa 1/0 para boolean
    )

    # Construtor: guardo nome, email e (opcionalmente) ativo
    def __init__(self, name, email, ativo=True):
        self.name = name
        self.email = email
        self.ativo = ativo

    # Transformo o objeto em dict para respostas JSON
    def json(self):
        return {
            "users_pk": self.users_pk,
            "name": self.name,
            "email": self.email,
            "ativo": self.ativo,
        }

    # Busco um usuário pela PK
    @classmethod
    def find_user(cls, users_pk):
        return cls.query.filter_by(users_pk=users_pk).first()

    # Busco um usuário pelo email
    @classmethod
    def find_by_email(cls, email):
        return cls.query.filter_by(email=email).first()

    # Salvo (insert/update) o usuário no banco
    def save_user(self):
        banco.session.add(self)
        banco.session.commit()

    # Excluo o usuário do banco
    def delete_user(self):
        banco.session.delete(self)
        banco.session.commit()

    # Atualizo apenas os campos enviados (não nulos) e já salvo
    def update_user(self, **kwargs):
        for key, value in kwargs.items():
            if value is not None:
                setattr(self, key, value)
        self.save_user()
