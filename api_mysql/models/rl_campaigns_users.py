from sql_alchemy import banco


class RlCampaignsUsersModel(banco.Model):
    __tablename__ = "rl_campaigns_users"

    rl_campaigns_users_pk = banco.Column(
        banco.Integer, primary_key=True, nullable=False
    )
    users_fk = banco.Column(banco.Integer, banco.ForeignKey("users.users_pk"))
    campaigns_fk = banco.Column(
        banco.Integer, banco.ForeignKey("campaigns.campaigns_pk"), nullable=True
    )
    party_roles_fk = banco.Column(
        banco.Integer, banco.ForeignKey("party_roles.party_roles_pk"), nullable=False
    )
    skus_fk = banco.Column(
        banco.Integer, banco.ForeignKey("skus.skus_pk"), nullable=False
    )
    start_date = banco.Column(banco.DateTime, nullable=False)
    active = banco.Column(banco.Boolean, nullable=False, default=True)

    def __init__(
        self,
        users_fk,
        campaigns_fk,
        party_roles_fk,
        skus_fk,
        start_date,
        active,
    ) -> None:

        self.users_fk = users_fk
        self.campaigns_fk = campaigns_fk
        self.party_roles_fk = party_roles_fk
        self.skus_fk = skus_fk
        self.start_date = start_date
        self.active = active

    def json(self):
        return {
            "rl_campaigns_users_pk": self.rl_campaigns_users_pk,
            "users_fk": self.users_fk,
            "campaigns_fk": self.campaigns_fk,
            "party_roles_fk": self.party_roles_fk,
            "skus_fk": self.skus_fk,
            "start_date": self.start_date.strftime("%Y-%m-%d"),
            "active": self.active,
        }

    @classmethod
    def find(cls, rl_campaigns_users_pk):
        rl_campaigns_user = cls.query.filter_by(
            rl_campaigns_users_pk=rl_campaigns_users_pk
        ).first()
        if rl_campaigns_user:
            return rl_campaigns_user
        return None

    @classmethod
    def find_by_user(cls, users_fk):
        rl_campaigns_user = cls.query.filter_by(users_fk=users_fk).first()
        if rl_campaigns_user:
            return rl_campaigns_user
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
