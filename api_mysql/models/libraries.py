from sql_alchemy import banco


class libraryModel(banco.Model):
    __tablename__ = "libraries"

    libraries_pk = banco.Column(banco.Integer, primary_key=True, nullable=False)
    users_fk = banco.Column(banco.Integer, banco.ForeignKey("users.users_pk"))
    skus_fk = banco.Column(
        banco.Integer, banco.ForeignKey("skus.skus_pk"), nullable=True
    )
    wish = banco.Column(banco.Boolean, nullable=False)
    owned = banco.Column(banco.Boolean, nullable=False)
    number = banco.Column(banco.Integer, nullable=True)
    active = banco.Column(banco.Boolean, nullable=False, default=True)

    def __init__(
        self,
        users_fk,
        skus_fk,
        wish,
        owned,
        number,
        active,
    ) -> None:

        self.users_fk = users_fk
        self.skus_fk = skus_fk
        self.wish = wish
        self.owned = owned
        self.number = number
        self.active = active

    def json(self):
        return {
            "libraries_pk": self.libraries_pk,
            "users_fk": self.users_fk,
            "skus_fk": self.skus_fk,
            "wish": self.wish,
            "owned": self.owned,
            "number": self.number,
            "active": self.active,
        }

    @classmethod
    def find_library(cls, libraries_pk):
        event = cls.query.filter_by(libraries_pk=libraries_pk).first()
        if event:
            return event
        return None

    @classmethod
    def find_by_user(cls, user_fk):
        rl_events_user = cls.query.filter_by(user=user_fk)
        if rl_events_user:
            return rl_events_user
        return None

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if value is not None:
                setattr(self, key, value)
        self.save()

    def save(self):
        banco.session.add(self)
        banco.session.commit()

    def delete(self):
        self.active = False
        banco.session.commit()

    def remove(self):
        banco.session.delete(self)
        banco.session.commit()
