from sql_alchemy import banco


class CampaignModel(banco.Model):
    __tablename__ = "campaigns"

    campaigns_pk = banco.Column(banco.Integer, primary_key=True)
    tracker_hash = banco.Column(banco.String(5000), nullable=False)
    conclusion_percentage = banco.Column(banco.Integer, nullable=True)
    party_name = banco.Column(banco.String(45), nullable=True)
    box = banco.Column(banco.String(45), nullable=False)
    active = banco.Column(banco.Boolean, nullable=False)

    def __init__(
        self,
        tracker_hash,
        conclusion_percentage,
        party_name,
        box,
        active,
    ) -> None:

        self.tracker_hash = tracker_hash
        self.conclusion_percentage = conclusion_percentage
        self.party_name = party_name
        self.box = box
        self.active = active

    def json(self):
        return {
            "campaigns_pk": self.campaigns_pk,
            "tracker_hash": self.tracker_hash,
            "conclusion_percentage": self.conclusion_percentage,
            "party_name": self.party_name,
            "box": self.box,
            "active": self.active,
        }

    @classmethod
    def find_campaign(cls, campaigns_pk):
        campaign = cls.query.filter_by(campaigns_pk=campaigns_pk).first()
        if campaign:
            return campaign
        return None

    @classmethod
    def find_by_party_name(cls, party_name):
        campaign = cls.query.filter_by(party_name=party_name).first()
        if campaign:
            return campaign
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
