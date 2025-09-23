from sql_alchemy import banco


class SkusModel(banco.Model):
    __tablename__ = "skus"

    skus_pk = banco.Column(banco.Integer, primary_key=True)
    name = banco.Column(banco.String(145), nullable=False)
    link = banco.Column(banco.String(200), nullable=False)
    color = banco.Column(banco.String(200), nullable=False)
    background = banco.Column(banco.String(200), nullable=False)
    picture_hash = banco.Column(banco.String(45), nullable=False)
    active = banco.Column(banco.Boolean, nullable=False)

    def __init__(
        self,
        name,
        link,
        color,
        background,
        picture_hash,
        active,
    ) -> None:

        self.link = link
        self.picture_hash = picture_hash
        self.name = name
        self.active = active
        self.color = color
        self.background = background

    def json(self):
        return {
            "skus_pk": self.skus_pk,
            "name": self.name,
            "link": self.link,
            "color": self.color,
            "background": self.background,
            "picture_hash": self.picture_hash,
            "active": self.active,
        }

    @classmethod
    def find_sku(cls, skus_pk):
        sku = cls.query.filter_by(skus_pk=skus_pk).first()
        if sku:
            return sku
        return None

    @classmethod
    def find_by_name(cls, name):
        sku = cls.query.filter_by(name=name).first()
        if sku:
            return sku
        return None

    def save_sku(self):
        banco.session.add(self)
        banco.session.commit()

    def delete_sku(self):
        self.active = False
        banco.session.commit()

    def remove_sku(self):
        banco.session.delete(self)
        banco.session.commit()
