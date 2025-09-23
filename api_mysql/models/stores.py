from sql_alchemy import banco


class StoreModel(banco.Model):
    __tablename__ = "stores"

    stores_pk = banco.Column(banco.Integer, primary_key=True)
    site = banco.Column(banco.String(145), nullable=True)
    name = banco.Column(banco.String(145), nullable=False)
    zip_code = banco.Column(banco.String(145), nullable=False)
    countries_fk = banco.Column(
        banco.Integer, banco.ForeignKey("countries.countries_pk"), nullable=False
    )
    users_fk = banco.Column(
        banco.Integer, banco.ForeignKey("users.users_pk"), nullable=False
    )
    address = banco.Column(banco.String(256), nullable=False)
    longitude = banco.Column(banco.Float, nullable=True)
    latitude = banco.Column(banco.Float, nullable=True)
    picture_hash = banco.Column(banco.String(145), nullable=True)
    web_site = banco.Column(banco.String(145), nullable=True)
    state = banco.Column(banco.String(100), nullable=True)
    merchant_id = banco.Column(banco.String(200), nullable=True)
    verified = banco.Column(banco.Boolean, nullable=False)
    active = banco.Column(banco.Boolean, nullable=False)

    def __init__(
        self,
        site,
        name,
        zip_code,
        countries_fk,
        users_fk,
        address,
        longitude,
        latitude,
        picture_hash,
        web_site,
        state,
        merchant_id,
        verified,
        active,
    ) -> None:
        self.site = site
        self.name = name
        self.zip_code = zip_code
        self.countries_fk = countries_fk
        self.users_fk = users_fk
        self.address = address
        self.longitude = longitude
        self.latitude = latitude
        self.picture_hash = picture_hash
        self.web_site = web_site
        self.state = state
        self.merchant_id = merchant_id
        self.verified = verified
        self.active = active

    def json(self):
        return {
            "stores_pk": self.stores_pk,
            "site": self.site,
            "name": self.name,
            "zip_code": self.zip_code,
            "countries_fk": self.countries_fk,
            "users_fk": self.users_fk,
            "address": self.address,
            "longitude": self.longitude,
            "latitude": self.latitude,
            "picture_hash": self.picture_hash,
            "web_site": self.web_site,
            "state": self.state,
            "merchant_id": self.merchant_id,
            "verified": self.verified,
            "active": self.active,
        }

    @classmethod
    def find_store(cls, stores_pk):
        store = cls.query.filter_by(stores_pk=stores_pk).first()
        if store:
            return store
        return None

    @classmethod
    def find_by_name(cls, party_name):
        store = cls.query.filter_by(party_name=party_name).first()
        if store:
            return store
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

    def verify(self):
        self.verified = True

        banco.session.commit()

    def remove(self):
        banco.session.delete(self)
        banco.session.commit()
