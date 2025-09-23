from sql_alchemy import banco


class rlEventsUsersModel(banco.Model):
    __tablename__ = "rl_events_users"

    rl_events_users_pk = banco.Column(banco.Integer, primary_key=True, nullable=False)
    users_fk = banco.Column(
        banco.Integer, banco.ForeignKey("users.users_pk"), nullable=False
    )
    events_fk = banco.Column(
        banco.Integer, banco.ForeignKey("events.events_pk"), nullable=False
    )
    status = banco.Column(
        banco.Integer, banco.ForeignKey("events.events_pk"), nullable=False
    )
    date = banco.Column(banco.DateTime, nullable=False)
    active = banco.Column(banco.Boolean, nullable=False, default=True)

    def __init__(
        self,
        users_fk,
        events_fk,
        status,
        date,
        active,
    ) -> None:

        self.users_fk = users_fk
        self.events_fk = events_fk
        self.status = status
        self.date = date
        self.active = active

    def json(self):
        return {
            "rl_events_users_pk": self.rl_events_users_pk,
            "users_fk": self.users_fk,
            "events_fk": self.events_fk,
            "status": self.status,
            "date": self.date.strftime("%Y-%m-%d; %I:%M %p"),
            "active": self.active,
        }

    @classmethod
    def find(cls, rl_events_users_pk):
        event = cls.query.filter_by(rl_events_users_pk=rl_events_users_pk).first()
        if event:
            return event
        return None

    @classmethod
    def find_event(cls, events_fk):
        event = cls.query.filter_by(events_fk=events_fk).first()
        if event:
            return event
        return None

    @classmethod
    def find_by_user(cls, user_fk):
        rl_events_user = cls.query.filter_by(user=user_fk).first()
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
