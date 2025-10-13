from sqlalchemy.ext.mutable import MutableList
from sqlalchemy import PickleType, JSON
from flask_login import UserMixin
from app.extensions import db
import hashlib

class Dimension(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    level = db.Column(db.Integer, nullable=False)
    parent = db.Column(db.Integer, db.ForeignKey('dimension.id'))
    
    children = db.relationship(
        'Dimension', 
        backref=db.backref('parent_ref', remote_side=[id]),
        foreign_keys=[parent]
    )
    
    questions = db.relationship('Question', back_populates='dimension')
    
    def __repr__(self):
        return f'<Dimension {self.name} (Level {self.level})>'

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dimension_id = db.Column(db.Integer, db.ForeignKey('dimension.id'), nullable=False)
    question_type = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text)
    
    dimension = db.relationship(
        'Dimension', 
        back_populates='questions',
        foreign_keys=[dimension_id]
    )
    answers = db.relationship('Answer', back_populates='question', cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Question {self.id}: {self.content[:50]}>'

class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    llm_id = db.Column(db.Integer, db.ForeignKey('llm.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    question = db.relationship('Question', back_populates='answers')
    ratings = db.relationship('Rating', back_populates='answer', cascade="all, delete-orphan")
    llm = db.relationship('LLM', backref='answers')
    
    def __repr__(self):
        return f'<Answer by {self.llm.name} for Q{self.question_id}>'

class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    answer_id = db.Column(db.Integer, db.ForeignKey('answer.id'), nullable=False)
    llm_id = db.Column(db.Integer, db.ForeignKey('llm.id'), nullable=False)
    score = db.Column(db.Float, nullable=False)
    comment = db.Column(db.Text)
    is_responsive = db.Column(db.Boolean, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    answer = db.relationship('Answer', back_populates='ratings')
    llm = db.relationship('LLM', backref='ratings')
    
    def __repr__(self):
        return f'<Rating {self.score} by {self.llm.name} for Answer {self.answer_id}>'

class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_type = db.Column(db.String(20), nullable=False)
    criteria = db.Column(db.Text, nullable=False)
    total_score = db.Column(db.Float, nullable=False, default=5.0)
    last_updated = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    def __repr__(self):
        return f'<Setting ({self.question_type}): {self.criteria[:50]}>'

class LLM(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    model = db.Column(db.String(100), nullable=False)
    base_url = db.Column(db.String(200), nullable=False)
    api_keys = db.Column(MutableList.as_mutable(PickleType), nullable=False)
    proxy = db.Column(db.String(200), default = '')
    desc = db.Column(db.Text, nullable=True)
    icon = db.Column(db.String(100), nullable=True)
    comment = db.Column(db.Text, nullable=True)
    
    
    def __repr__(self):
        return f'<LLM {self.name} ({self.model})>'

class EvaluationHistory(db.Model):
    """评估历史记录表，存储每次更新全部模型后的快照数据"""
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp(), nullable=False)
    
    dimensions = db.Column(JSON, nullable=False)
    
    evaluation_data = db.Column(JSON, nullable=False)
    
    extra_info = db.Column(JSON, nullable=True)
    
    @property
    def date_for_grouping(self):
        return self.timestamp.date()

    def __repr__(self):
        return f'<EvaluationHistory {self.timestamp}>'
    
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False, nullable=False)

    def set_password(self, password):
        self.password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()

    def check_password(self, password):
        return self.password_hash == hashlib.sha256(password.encode('utf-8')).hexdigest()
