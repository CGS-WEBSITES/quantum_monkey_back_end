from sql_alchemy import banco
from sqlalchemy import Boolean, text


# Modelo da tabela de contatos (e-mail + nome + list_id + ativo)
class ContactModel(banco.Model):
    __tablename__ = "contacts"
    __table_args__ = (
        banco.UniqueConstraint("email", "list_id", name="uq_email_list"),
    )

    contacts_pk = banco.Column(banco.Integer, primary_key=True)
    email = banco.Column(banco.String(320), nullable=False, index=True)
    # Nome do contato (opcional)
    name = banco.Column(banco.String(145), nullable=True)
    # Lista de e-mail ao qual o contato pertence (default 1 - Marketing)
    list_id = banco.Column(
        banco.Integer,
        banco.ForeignKey("email_lists.id"),
        nullable=False,
        default=1,
        server_default=text("1"),
    )
    # Indica se o contato está ativo (default True)
    ativo = banco.Column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("1"),  # MySQL/MariaDB usam 1/0 para boolean
    )

    def __init__(self, email, name=None, list_id=1, ativo=True):
        self.email = (email or "").strip().lower()
        self.name = (name or "").strip() or None
        self.list_id = int(list_id) if list_id else 1
        self.ativo = True if ativo is None else bool(ativo)

    def json(self):
        return {
            "contacts_pk": self.contacts_pk,
            "email": self.email,
            "name": self.name,
            "list_id": self.list_id,
            "ativo": self.ativo,
        }

    @classmethod
    def find(cls, contacts_pk):
        return cls.query.filter_by(contacts_pk=contacts_pk).first()

    @classmethod
    def find_by_email(cls, email, list_id=None):
        query = cls.query.filter_by(email=(email or "").strip().lower())
        if list_id is not None:
            query = query.filter_by(list_id=list_id)
        return query.first()

    def save(self):
        banco.session.add(self)
        banco.session.commit()

    def delete(self):
        banco.session.delete(self)
        banco.session.commit()

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if value is None:
                continue
            if key == "email":
                value = (value or "").strip().lower()
            elif key == "name":
                value = (value or "").strip() or None
            elif key == "list_id":
                value = int(value)
            elif key == "ativo":
                value = bool(value)
            setattr(self, key, value)
        self.save()

