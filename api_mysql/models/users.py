from sql_alchemy import banco
from sqlalchemy import Boolean, text
from bcryptInit import bcrypt  # Importar o bcrypt do seu arquivo


class UserModel(banco.Model):
    __tablename__ = "users"

    users_pk = banco.Column(banco.Integer, primary_key=True)
    name = banco.Column(banco.String(145), nullable=False)
    email = banco.Column(banco.String(320), nullable=False, unique=True)
    password = banco.Column(
        banco.String(255), nullable=False
    )  # NOVO: senha hasheada
    active = banco.Column(
        Boolean,
        nullable=False,
        default=True,
    )

    def __init__(self, name, email, password=None, active=True):
        self.name = name
        self.email = email
        if password:
            self.password = bcrypt.generate_password_hash(password).decode("utf-8")
        self.active = active

    def json(self):
        return {
            "users_pk": self.users_pk,
            "name": self.name,
            "email": self.email,
            "active": self.active,
        }

    def verify_password(self, password):
        """Verifica se a senha está correta"""
        return bcrypt.check_password_hash(self.password, password)

    def set_password(self, password):
        """Atualiza a senha do usuário"""
        self.password = bcrypt.generate_password_hash(password).decode("utf-8")

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
                if key == "password":
                    self.set_password(value)
                else:
                    setattr(self, key, value)
        self.save_user()
