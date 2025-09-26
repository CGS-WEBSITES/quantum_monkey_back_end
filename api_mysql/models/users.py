from sql_alchemy import banco


class UserModel(banco.Model):
    __tablename__ = "users"

    users_pk = banco.Column(banco.Integer, primary_key=True)
    name = banco.Column(banco.String(145), nullable=False)
    email = banco.Column(banco.String(320), nullable=False, unique=True)

    def __init__(self, name, email):
        self.name = name
        self.email = email

    def json(self):
        return {
            "users_pk": self.users_pk, "name": self.name, "email": self.email,
        }

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
                setattr(self, key, value)
        self.save_user()
