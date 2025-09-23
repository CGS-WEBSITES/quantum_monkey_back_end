from sql_alchemy import banco


class CountriesModel(banco.Model):
    __tablename__ = "countries"

    countries_pk = banco.Column(banco.Integer, primary_key=True)
    name = banco.Column(banco.String(145), nullable=False, unique=True)
    abbreviation = banco.Column(banco.String(3), nullable=False, unique=True)
    active = banco.Column(banco.Boolean, nullable=False)

    def __init__(
        self,
        name,
        abbreviation,
        active,
    ) -> None:

        self.abbreviation = abbreviation
        self.name = name
        self.active = active

    def json(self):
        return {
            "countries_pk": self.countries_pk,
            "name": self.name,
            "abbreviation": self.abbreviation,
            "active": self.active,
        }

    @classmethod
    def find_country(cls, countries_pk):
        country = cls.query.filter_by(countries_pk=countries_pk).first()
        if country:
            return country
        return None

    @classmethod
    def find_by_name(cls, name):
        country = cls.query.filter_by(name=name).first()
        if country:
            return country
        return None

    @classmethod
    def find_by_abbrevitaion(cls, abbrevitaion):
        country = cls.query.filter_by(abbrevitaion=abbrevitaion).first()
        if country:
            return country
        return None

    def save_country(self):
        banco.session.add(self)
        banco.session.commit()

    def delete_country(self):
        self.active = False
        banco.session.commit()

    def remove_country(self):
        banco.session.delete(self)
        banco.session.commit()
