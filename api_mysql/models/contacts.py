from sql_alchemy import banco


# Modelo da tabela de contatos (somente e-mail)
class ContactModel(banco.Model):
    __tablename__ = "contacts"

    contacts_pk = banco.Column(banco.Integer, primary_key=True)
    email = banco.Column(
      banco.String(320), nullable=False, unique=True, index=True)

    def __init__(self, email):
        self.email = (email or "").strip().lower()

    def json(self):
        return {
            "contacts_pk": self.contacts_pk,
            "email": self.email,
        }

    @classmethod
    def find(cls, contacts_pk):
        return cls.query.filter_by(contacts_pk=contacts_pk).first()

    @classmethod
    def find_by_email(cls, email):
        return cls.query.filter_by(email=(email or "").strip().lower()).first()

    def save(self):
        banco.session.add(self)
        banco.session.commit()

    def delete(self):
        banco.session.delete(self)
        banco.session.commit()

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if value is not None:
                if key == "email":
                    value = (value or "").strip().lower()
                setattr(self, key, value)
        self.save()
