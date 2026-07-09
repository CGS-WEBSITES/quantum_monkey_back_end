from sql_alchemy import banco
from datetime import datetime

class EmailLogModel(banco.Model):
    __tablename__ = "email_logs"

    id = banco.Column(banco.Integer, primary_key=True)
    subject = banco.Column(banco.String(255), nullable=False)
    recipient_count = banco.Column(banco.Integer, nullable=False)
    sent_count = banco.Column(banco.Integer, nullable=False, default=0)
    failed_count = banco.Column(banco.Integer, nullable=False, default=0)
    sent_at = banco.Column(banco.DateTime, nullable=False, default=datetime.utcnow)
    status = banco.Column(banco.String(50), nullable=False, default="Sending")

    def __init__(self, subject, recipient_count, status="Sending", sent_count=0, failed_count=0):
        self.subject = subject
        self.recipient_count = recipient_count
        self.status = status
        self.sent_count = sent_count
        self.failed_count = failed_count
        self.sent_at = datetime.utcnow()

    def json(self):
        return {
            "id": self.id,
            "subject": self.subject,
            "recipient_count": self.recipient_count,
            "sent_count": self.sent_count,
            "failed_count": self.failed_count,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "status": self.status
        }

    def save(self):
        banco.session.add(self)
        banco.session.commit()

    def update(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        banco.session.commit()
