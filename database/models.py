from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from database.database import Base, db

class ReviewLog(db.Model):
    __tablename__ = 'review_logs'  
    
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.String(100), nullable=False)
    decision = db.Column(db.String(50), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class NetworkCase(Base):
    __tablename__ = "network_cases"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String(50), unique=True, index=True)
    category = Column(String(50))
    symptom = Column(Text)
    topology_note = Column(Text)
    show_outputs = Column(Text)
    expected_root_cause = Column(Text)
    fix_steps = Column(Text)

class DiagnosticRecord(db.Model):
    __tablename__ = 'diagnostic_records'
    
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.String(50), nullable=False)
    symptom = db.Column(db.Text, nullable=False)
    topology_note = db.Column(db.Text, nullable=True)
    show_outputs = db.Column(db.Text, nullable=True)
    ai_root_cause = db.Column(db.Text, nullable=True)
    confidence = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "case_id": self.case_id,
            "symptom": self.symptom,
            "ai_root_cause": self.ai_root_cause,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class HumanReviewLog(db.Model):
    __tablename__ = 'human_review_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.String(50), nullable=False)
    decision = db.Column(db.String(20), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    reviewed_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "case_id": self.case_id,
            "decision": self.decision,
            "notes": self.notes,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None
        }