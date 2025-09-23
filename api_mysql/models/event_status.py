from sql_alchemy import banco


class EventStatusModel(banco.Model):
    __tablename__ = "event_status"

    event_status_pk = banco.Column(banco.Integer, primary_key=True)
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
            "event_status_pk": self.event_status_pk,
            "name": self.name,
            "active": self.active,
        }

    @classmethod
    def find_status(cls, event_status_pk):
        status = cls.query.filter_by(event_status_pk=event_status_pk).first()
        if status:
            return status
        return None

    @classmethod
    def find_by_name(cls, name):
        status = cls.query.filter_by(name=name).first()
        if status:
            return status
        return None

    def save_status(self):
        banco.session.add(self)
        banco.session.commit()

    def delete_status(self):
        self.active = False
        banco.session.commit()

    def remove_status(self):
        banco.session.delete(self)
        banco.session.commit()
