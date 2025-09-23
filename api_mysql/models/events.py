from sql_alchemy import banco


class eventModel(banco.Model):
    __tablename__ = "events"

    events_pk = banco.Column(banco.Integer, primary_key=True)
    seats_number = banco.Column(banco.Integer, nullable=False)
    seasons_fk = banco.Column(
        banco.Integer, banco.ForeignKey("seasons.seasons_pk"), nullable=False
    )
    sceneries_fk = banco.Column(
        banco.Integer, banco.ForeignKey("sceneries.sceneries_pk"), nullable=False
    )
    date = banco.Column(banco.DateTime, nullable=False)
    stores_fk = banco.Column(
        banco.Integer, banco.ForeignKey("stores.stores_pk"), nullable=False
    )
    users_fk = banco.Column(
        banco.Integer, banco.ForeignKey("users.users_pk"), nullable=False
    )
    active = banco.Column(banco.Boolean, nullable=False)

    def __init__(
        self,
        seats_number,
        seasons_fk,
        sceneries_fk,
        date,
        stores_fk,
        users_fk,
        active,
    ) -> None:

        self.seats_number = seats_number
        self.seasons_fk = seasons_fk
        self.sceneries_fk = sceneries_fk
        self.date = date
        self.stores_fk = stores_fk
        self.users_fk = users_fk
        self.active = active

    def json(self):
        return {
            "events_pk": self.events_pk,
            "seats_number": self.seats_number,
            "seasons_fk": self.seasons_fk,
            "sceneries_fk": self.sceneries_fk,
            "date": self.date.strftime("%Y-%m-%d; %I:%M %p"),
            "stores_fk": self.stores_fk,
            "users_fk": self.users_fk,
            "active": self.active,
        }

    @classmethod
    def find_event(cls, events_pk):
        event = cls.query.filter_by(events_pk=events_pk).first()
        if event:
            return event
        return None

    @classmethod
    def find_by_name(cls, party_name):
        event = cls.query.filter_by(party_name=party_name).first()
        if event:
            return event
        return None

    def save(self):
        banco.session.add(self)
        banco.session.commit()

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if value is not None:
                setattr(self, key, value)
        self.save()

    def delete(self):
        self.active = False
        banco.session.commit()

    def remove(self):
        banco.session.delete(self)
        banco.session.commit()
