from sql_alchemy import banco


class friendModel(banco.Model):
    __tablename__ = "friends"

    friends_pk = banco.Column(banco.Integer, primary_key=True, nullable=False)
    invite_users_fk = banco.Column(
        banco.Integer, banco.ForeignKey("users.users_pk"), nullable=False
    )
    recipient_users_fk = banco.Column(
        banco.Integer, banco.ForeignKey("users.users_pk"), nullable=False
    )
    accepted = banco.Column(banco.Boolean, nullable=False)
    active = banco.Column(banco.Boolean, nullable=False, default=True)

    def __init__(
        self,
        invite_users_fk,
        recipient_users_fk,
        accepted,
        active,
    ) -> None:

        self.invite_users_fk = invite_users_fk
        self.recipient_users_fk = recipient_users_fk
        self.accepted = accepted
        self.active = active

    def json(self):
        return {
            "friends_pk": self.friends_pk,
            "invite_users_fk": self.invite_users_fk,
            "recipient_users_fk": self.recipient_users_fk,
            "accepted": self.accepted,
            "active": self.active,
        }

    @classmethod
    def find_by_pk(cls, friends_pk):
        friend = cls.query.filter_by(friends_pk=friends_pk).first()
        if friend:
            return friend
        return None

    @classmethod
    def find_friend(cls, invite_users_fk, recipient_users_fk):
        friend = cls.query.filter(
            cls.invite_users_fk == invite_users_fk,
            cls.recipient_users_fk == recipient_users_fk,
        ).first()
        if friend:
            return friend
        return None

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if value is not None:
                setattr(self, key, value)
        self.save()

    def save(self):
        banco.session.add(self)
        banco.session.commit()

    def accept(self):
        self.accepted = True
        banco.session.commit()

    def delete(self):
        self.active = False
        banco.session.commit()

    def remove(self):
        banco.session.delete(self)
        banco.session.commit()
