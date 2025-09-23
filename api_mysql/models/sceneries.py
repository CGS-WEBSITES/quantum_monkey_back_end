from sql_alchemy import banco


class SceneriesModel(banco.Model):
    __tablename__ = "sceneries"

    sceneries_pk = banco.Column(banco.Integer, primary_key=True)
    name = banco.Column(banco.String(145), nullable=False)
    sceneries_hash = banco.Column(banco.String(145), nullable=True)
    active = banco.Column(banco.Boolean, nullable=False)

    def __init__(
        self,
        name,
        sceneries_hash,
        active,
    ) -> None:

        self.name = name
        self.sceneries_hash = sceneries_hash
        self.active = active

    def json(self):
        return {
            "sceneries_pk": self.sceneries_pk,
            "name": self.name,
            "sceneries_hash": self.sceneries_hash,
            "active": self.active,
        }

    @classmethod
    def find_season(cls, sceneries_pk):
        season = cls.query.filter_by(sceneries_pk=sceneries_pk).first()
        if season:
            return season
        return None

    @classmethod
    def find_by_name(cls, name):
        season = cls.query.filter_by(name=name).first()
        if season:
            return season
        return None

    def save(self):
        banco.session.add(self)
        banco.session.commit()

    def delete(self):
        self.active = False
        banco.session.commit()

    def remove(self):
        banco.session.delete(self)
        banco.session.commit()
