from sql_alchemy import banco


class RewardsModel(banco.Model):
    __tablename__ = "rewards"

    rewards_pk = banco.Column(banco.Integer, primary_key=True)
    name = banco.Column(banco.String(145), nullable=False)
    picture_hash = banco.Column(banco.String(145), nullable=False)
    description = banco.Column(banco.String(250), nullable=False)
    active = banco.Column(banco.Boolean, nullable=False)

    def __init__(
        self,
        name,
        picture_hash,
        description,
        active,
    ) -> None:

        self.picture_hash = picture_hash
        self.description = description
        self.name = name
        self.active = active

    def json(self):
        return {
            "rewards_pk": self.rewards_pk,
            "name": self.name,
            "picture_hash": self.picture_hash,
            "description": self.description,
            "active": self.active,
        }

    @classmethod
    def find(cls, rewards_pk):
        reward = cls.query.filter_by(rewards_pk=rewards_pk).first()
        if reward:
            return reward
        return None

    @classmethod
    def find_by_name(cls, name):
        reward = cls.query.filter_by(name=name).first()
        if reward:
            return reward
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
