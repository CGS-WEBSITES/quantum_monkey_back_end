from sql_alchemy import banco


class rlUsersRewardsModel(banco.Model):
    __tablename__ = "rl_users_rewards"

    rl_users_rewards_pk = banco.Column(banco.Integer, primary_key=True, nullable=False)
    users_fk = banco.Column(
        banco.Integer, banco.ForeignKey("users.users_pk"), nullable=False
    )
    rewards_fk = banco.Column(
        banco.Integer, banco.ForeignKey("rewards.rewards_pk"), nullable=False
    )
    date = banco.Column(banco.DateTime, nullable=False)
    active = banco.Column(banco.Boolean, nullable=False, default=True)

    def __init__(
        self,
        users_fk,
        rewards_fk,
        date,
        active,
    ) -> None:

        self.users_fk = users_fk
        self.rewards_fk = rewards_fk
        self.date = date
        self.active = active

    def json(self):
        return {
            "rl_users_rewards_pk": self.rl_users_rewards_pk,
            "users_fk": self.users_fk,
            "rewards_fk": self.rewards_fk,
            "date": self.date.strftime("%Y-%m-%d; %I:%M %p"),
            "active": self.active,
        }

    @classmethod
    def find(cls, rl_users_rewards_pk):
        user = cls.query.filter_by(rl_users_rewards_pk=rl_users_rewards_pk).first()
        if user:
            return user
        return None

    @classmethod
    def find_by_user(cls, users_fk):
        user = cls.query.filter_by(users_fk=users_fk).first()
        if user:
            return user
        return None

    @classmethod
    def find_by_reward(cls, reward_fk):
        rl_users_reward = cls.query.filter_by(reward=reward_fk).first()
        if rl_users_reward:
            return rl_users_reward
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
