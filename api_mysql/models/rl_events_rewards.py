from sql_alchemy import banco


class rlEventsRewardsModel(banco.Model):
    __tablename__ = "rl_events_rewards"

    rl_events_rewards_pk = banco.Column(banco.Integer, primary_key=True, nullable=False)
    events_fk = banco.Column(
        banco.Integer, banco.ForeignKey("events.events_pk"), nullable=False
    )
    rewards_fk = banco.Column(
        banco.Integer, banco.ForeignKey("rewards.rewards_pk"), nullable=False
    )
    active = banco.Column(banco.Boolean, nullable=False, default=True)

    def __init__(
        self,
        events_fk,
        rewards_fk,
        active,
    ) -> None:

        self.events_fk = events_fk
        self.rewards_fk = rewards_fk
        self.active = active

    def json(self):
        return {
            "rl_events_rewards_pk": self.rl_events_rewards_pk,
            "events_fk": self.events_fk,
            "rewards_fk": self.rewards_fk,
            "active": self.active,
        }

    @classmethod
    def find(cls, rl_events_rewards_pk):
        event = cls.query.filter_by(rl_events_rewards_pk=rl_events_rewards_pk).first()
        if event:
            return event
        return None

    @classmethod
    def find_by_event(cls, events_fk):
        event = cls.query.filter_by(events_fk=events_fk).first()
        if event:
            return event
        return None

    @classmethod
    def find_by_reward(cls, reward_fk):
        rl_events_reward = cls.query.filter_by(reward=reward_fk).first()
        if rl_events_reward:
            return rl_events_reward
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
