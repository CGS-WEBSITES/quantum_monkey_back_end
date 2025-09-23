from sql_alchemy import banco


class SeasonsModel(banco.Model):
    __tablename__ = "seasons"

    seasons_pk = banco.Column(banco.Integer, primary_key=True)
    name = banco.Column(banco.String(145), nullable=False)
    season_hash = banco.Column(banco.String(145), nullable=True)
    active = banco.Column(banco.Boolean, nullable=False)

    def __init__(
        self,
        name,
        season_hash,
        active,
    ) -> None:

        self.name = name
        self.season_hash = season_hash
        self.active = active

    def json(self):
        return {
            "seasons_pk": self.seasons_pk,
            "name": self.name,
            "season_hash": self.season_hash,
            "active": self.active,
        }

    @classmethod
    def find_season(cls, seasons_pk):
        season = cls.query.filter_by(seasons_pk=seasons_pk).first()
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
