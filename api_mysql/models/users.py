from sql_alchemy import banco


class UserModel(banco.Model):
    __tablename__ = "users"

    users_pk = banco.Column(banco.Integer, primary_key=True)
    name = banco.Column(banco.String(145), nullable=False)
    email = banco.Column(banco.String(320), nullable=False, unique=True)
    password = banco.Column(banco.String(200), nullable=False)
    active = banco.Column(banco.Boolean, nullable=False)
    verified = banco.Column(banco.Boolean, nullable=False)

    def __init__(
        self,
        name,
        user_name,
        email,
        password,
        active,
        verified,
    ) -> None:

        self.name = name
        self.user_name = user_name
        self.email = email
        self.password = password
        self.active = active
        self.verified = verified

    def json(self):
        return {
            "users_pk": self.users_pk,
            "name": self.name,
            "user_name": self.user_name,
            "email": self.email,
            "active": self.active,
            "verified": self.verified,
        }

    @classmethod
    def find_user(cls, users_pk):
        user = cls.query.filter_by(users_pk=users_pk).first()
        if user:
            return user
        return None

    @classmethod
    def find_by_name(cls, name):
        user = cls.query.filter_by(name=name).first()
        if user:
            return user
        return None

    @classmethod
    def find_by_email(cls, email):
        user = cls.query.filter_by(email=email).first()

        if user:
            return user

        return None

    def update_pwd(self, password):
        self.password = password
        self.save_user()

    def update_user(self, **kwargs):
        for key, value in kwargs.items():
            if value is not None:
                setattr(self, key, value)
        self.save_user()

    def save_user(self):
        banco.session.add(self)
        banco.session.commit()

    def delete_user(self):
        self.active = False
        self.save_user()

    def remove_user(self):
        banco.session.delete(self)
        banco.session.commit()
