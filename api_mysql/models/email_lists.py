from sql_alchemy import banco
from sqlalchemy import Boolean, text


class EmailListModel(banco.Model):
    __tablename__ = "email_lists"

    id = banco.Column(banco.Integer, primary_key=True)
    name = banco.Column(banco.String(100), nullable=False)
    description = banco.Column(banco.String(255), nullable=True)
    slug = banco.Column(banco.String(100), nullable=False, default="marketing")
    created_at = banco.Column(banco.DateTime, server_default=banco.func.now())
    ativo = banco.Column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("1"),
    )

    contacts = banco.relationship("ContactModel", backref="email_list", lazy="dynamic")

    def __init__(self, name, description=None, slug=None, ativo=True):
        self.name = (name or "").strip()
        self.description = (description or "").strip() or None
        if slug:
            self.slug = slug.strip().lower()
        else:
            self.slug = (name or "").strip().lower().replace(" ", "-")
        self.ativo = True if ativo is None else bool(ativo)

    def json(self):
        active_contacts_count = self.contacts.filter_by(ativo=True).count()
        total_contacts_count = self.contacts.count()
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "slug": self.slug,
            "ativo": self.ativo,
            "contacts_count": active_contacts_count,
            "total_contacts": total_contacts_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def find_by_id(cls, list_id):
        return cls.query.filter_by(id=list_id).first()

    @classmethod
    def find_by_slug(cls, slug):
        return cls.query.filter_by(slug=(slug or "").strip().lower()).first()

    @classmethod
    def get_or_create_default(cls):
        default_list = cls.query.order_by(cls.id.asc()).first()
        if not default_list:
            default_list = cls(
                name="Marketing",
                description="Lista padrão de Marketing",
                slug="marketing",
                ativo=True,
            )
            banco.session.add(default_list)
            banco.session.commit()
        return default_list

    def save(self):
        banco.session.add(self)
        banco.session.commit()

    def delete(self):
        self.ativo = False
        self.save()

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if value is None and key != "description":
                continue
            if key == "name":
                setattr(self, key, (value or "").strip())
            elif key == "description":
                setattr(self, key, (value or "").strip() or None)
            elif key == "slug":
                setattr(self, key, (value or "").strip().lower())
            elif key == "ativo":
                setattr(self, key, bool(value))
        self.save()
