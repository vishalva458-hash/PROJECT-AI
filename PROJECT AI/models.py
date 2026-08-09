from datetime import datetime
import json
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    resumes = db.relationship('Resume', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    sessions = db.relationship('InterviewSession', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_latest_resume(self):
        return self.resumes.order_by(Resume.uploaded_at.desc()).first()

    def __repr__(self):
        return f'<User {self.username}>'


class Resume(db.Model):
    __tablename__ = 'resumes'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(512), nullable=False)
    extracted_text = db.Column(db.Text, nullable=True)
    _skills = db.Column('skills', db.Text, nullable=True)  # Stored as JSON string
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def skills(self):
        if not self._skills:
            return []
        try:
            return json.loads(self._skills)
        except Exception:
            return []

    @skills.setter
    def skills(self, skill_list):
        if isinstance(skill_list, list):
            self._skills = json.dumps(skill_list)
        else:
            self._skills = json.dumps([])

    def __repr__(self):
        return f'<Resume {self.filename} for User {self.user_id}>'


class InterviewSession(db.Model):
    __tablename__ = 'interview_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    target_role = db.Column(db.String(100), nullable=False)
    experience_level = db.Column(db.String(50), default='Mid Level') # Entry, Mid Level, Senior, Lead
    total_score = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='in_progress') # 'in_progress', 'completed'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    questions = db.relationship('QuestionAnswer', backref='session', lazy='joined', cascade='all, delete-orphan', order_by='QuestionAnswer.question_num')

    def calculate_overall_score(self):
        q_list = QuestionAnswer.query.filter_by(session_id=self.id).all() if self.id else self.questions
        answered = [q for q in q_list if q.score is not None]
        if not answered:
            self.total_score = 0.0
        else:
            self.total_score = round(sum(q.score for q in answered) / len(answered), 1)
        return self.total_score

    def __repr__(self):
        return f'<InterviewSession {self.id} Role: {self.target_role}>'


class QuestionAnswer(db.Model):
    __tablename__ = 'question_answers'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('interview_sessions.id'), nullable=False)
    question_num = db.Column(db.Integer, nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), default='Technical') # Technical, Behavioral, System Design, Problem Solving
    user_answer = db.Column(db.Text, nullable=True)
    score = db.Column(db.Float, nullable=True) # 0 to 100
    feedback = db.Column(db.Text, nullable=True)
    _strengths = db.Column('strengths', db.Text, nullable=True)
    _improvements = db.Column('improvements', db.Text, nullable=True)
    sample_answer = db.Column(db.Text, nullable=True)
    answered_at = db.Column(db.DateTime, nullable=True)

    @property
    def strengths(self):
        if not self._strengths:
            return []
        try:
            return json.loads(self._strengths)
        except Exception:
            return []

    @strengths.setter
    def strengths(self, items):
        self._strengths = json.dumps(items if isinstance(items, list) else [])

    @property
    def improvements(self):
        if not self._improvements:
            return []
        try:
            return json.loads(self._improvements)
        except Exception:
            return []

    @improvements.setter
    def improvements(self, items):
        self._improvements = json.dumps(items if isinstance(items, list) else [])

    def __repr__(self):
        return f'<QuestionAnswer Q{self.question_num} Session {self.session_id}>'
