from sql_alchemy import banco


class RolesModel(banco.Model):
    __tablename__ = "roles"

    roles_pk = banco.Column(banco.Integer, primary_key=True)
    name = banco.Column(banco.String(145), nullable=False)
    active = banco.Column(banco.Boolean, nullable=False)

    def __init__(
        self,
        name,
        active,
    ) -> None:

        self.name = name
        self.active = active

    def json(self):
        return {
            "roles_pk": self.roles_pk,
            "name": self.name,
            "active": self.active,
        }

    @classmethod
    def find_role(cls, roles_pk):
        role = cls.query.filter_by(roles_pk=roles_pk).first()
        if role:
            return role
        return None

    @classmethod
    def find_by_name(cls, name):
        role = cls.query.filter_by(name=name).first()
        if role:
            return role
        return None

    def save_role(self):
        banco.session.add(self)
        banco.session.commit()

    def delete_role(self):
        self.active = False
        banco.session.commit()

    def remove_role(self):
        banco.session.delete(self)
        banco.session.commit()
