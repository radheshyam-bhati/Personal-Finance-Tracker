from datetime import datetime
from decimal import Decimal
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager
import hashlib

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    
    categories = db.relationship('Category', backref='user', lazy=True, cascade='all, delete-orphan')
    transactions = db.relationship('Transaction', backref='user', lazy=True, cascade='all, delete-orphan')
    category_rules = db.relationship('CategoryRule', backref='user', lazy=True, cascade='all, delete-orphan')
    goals = db.relationship('Goal', backref='user', lazy=True, cascade='all, delete-orphan')
    import_batches = db.relationship('ImportBatch', backref='user', lazy=True, cascade='all, delete-orphan')
    audit_logs = db.relationship('AuditLog', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256:12', salt_length=16)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.email}>'

class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    is_default = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    transactions = db.relationship('Transaction', backref='category', lazy=True)
    rules = db.relationship('CategoryRule', backref='category', lazy=True, cascade='all, delete-orphan')
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'name', name='uq_user_category_name'),
        db.Index('ix_category_user_name', 'user_id', 'name'),
    )
    
    DEFAULT_CATEGORIES = [
        ('Salary', True), ('Freelance', True), ('Investments', True), ('Gifts', True), ('Other Income', True),
        ('Housing', False), ('Food', False), ('Transportation', False), ('Utilities', False),
        ('Entertainment', False), ('Healthcare', False), ('Shopping', False), ('Education', False), ('Other Expense', False),
        ('Uncategorized', False)
    ]
    
    @classmethod
    def seed_default_categories(cls, user_id):
        for name, is_income in cls.DEFAULT_CATEGORIES:
            cat = cls(user_id=user_id, name=name, is_default=True)
            db.session.add(cat)
        db.session.commit()
    
    def __repr__(self):
        return f'<Category {self.name}>'

class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id', ondelete='SET NULL'), nullable=True, index=True)
    date = db.Column(db.Date, nullable=False, index=True)
    description = db.Column(db.String(500), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    type = db.Column(db.String(10), nullable=False)  # 'income' or 'expense'
    source = db.Column(db.String(20), nullable=False, default='manual')  # 'manual' or 'csv_import'
    import_batch_id = db.Column(db.Integer, db.ForeignKey('import_batches.id', ondelete='SET NULL'), nullable=True)
    dedup_hash = db.Column(db.String(64), nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.CheckConstraint("type IN ('income', 'expense')", name='ck_transaction_type'),
        db.CheckConstraint("source IN ('manual', 'csv_import')", name='ck_transaction_source'),
        db.Index('ix_transaction_user_date', 'user_id', 'date'),
        db.Index('ix_transaction_user_category', 'user_id', 'category_id'),
    )
    
    @staticmethod
    def compute_dedup_hash(user_id, date, amount, description):
        normalized_desc = description.strip().lower()
        data = f"{user_id}|{date}|{amount}|{normalized_desc}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    def __repr__(self):
        return f'<Transaction {self.date} {self.type} {self.amount}>'

class CategoryRule(db.Model):
    __tablename__ = 'category_rules'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id', ondelete='CASCADE'), nullable=False)
    keyword = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    __table_args__ = (
        db.Index('ix_category_rule_user_keyword', 'user_id', 'keyword'),
    )
    
    DEFAULT_RULES = [
        ('salary', 'Salary'), ('payroll', 'Salary'), ('wage', 'Salary'), ('income', 'Salary'),
        ('freelance', 'Freelance'), ('contract', 'Freelance'), ('gig', 'Freelance'),
        ('dividend', 'Investments'), ('interest', 'Investments'), ('investment', 'Investments'),
        ('gift', 'Gifts'), ('present', 'Gifts'),
        ('rent', 'Housing'), ('mortgage', 'Housing'), ('lease', 'Housing'),
        ('grocery', 'Food'), ('groceries', 'Food'), ('supermarket', 'Food'), ('food', 'Food'), ('restaurant', 'Food'), ('dining', 'Food'),
        ('uber', 'Transportation'), ('lyft', 'Transportation'), ('taxi', 'Transportation'), ('transit', 'Transportation'), ('bus', 'Transportation'), ('train', 'Transportation'), ('gas', 'Transportation'), ('fuel', 'Transportation'),
        ('electric', 'Utilities'), ('electricity', 'Utilities'), ('water', 'Utilities'), ('gas bill', 'Utilities'), ('internet', 'Utilities'), ('phone', 'Utilities'), ('utility', 'Utilities'),
        ('netflix', 'Entertainment'), ('spotify', 'Entertainment'), ('hulu', 'Entertainment'), ('disney', 'Entertainment'), ('movie', 'Entertainment'), ('theater', 'Entertainment'), ('game', 'Entertainment'),
        ('doctor', 'Healthcare'), ('pharmacy', 'Healthcare'), ('hospital', 'Healthcare'), ('medical', 'Healthcare'), ('dental', 'Healthcare'), ('vision', 'Healthcare'), ('health', 'Healthcare'),
        ('amazon', 'Shopping'), ('target', 'Shopping'), ('walmart', 'Shopping'), ('costco', 'Shopping'), ('store', 'Shopping'), ('shop', 'Shopping'),
        ('tuition', 'Education'), ('course', 'Education'), ('book', 'Education'), ('school', 'Education'), ('education', 'Education'),
    ]
    
    @classmethod
    def seed_default_rules(cls, user_id):
        categories = {c.name: c.id for c in Category.query.filter_by(user_id=user_id).all()}
        for keyword, cat_name in cls.DEFAULT_RULES:
            if cat_name in categories:
                rule = cls(user_id=user_id, category_id=categories[cat_name], keyword=keyword)
                db.session.add(rule)
        db.session.commit()
    
    def __repr__(self):
        return f'<CategoryRule {self.keyword} -> {self.category_id}>'

class Goal(db.Model):
    __tablename__ = 'goals'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    target_amount = db.Column(db.Numeric(12, 2), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    target_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.CheckConstraint('target_amount > 0', name='ck_goal_target_amount_positive'),
        db.CheckConstraint('target_date > start_date', name='ck_goal_target_after_start'),
    )
    
    def calculate_progress(self):
        from app.analytics.services import FinanceAnalytics
        analytics = FinanceAnalytics(self.user_id)
        return analytics.get_goal_progress(self)
    
    def __repr__(self):
        return f'<Goal {self.name} - {self.target_amount}>'

class ImportBatch(db.Model):
    __tablename__ = 'import_batches'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    row_count = db.Column(db.Integer, nullable=False)
    rows_imported = db.Column(db.Integer, nullable=False)
    rows_flagged = db.Column(db.Integer, nullable=False, default=0)
    imported_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    transactions = db.relationship('Transaction', backref='import_batch', lazy=True)
    
    def __repr__(self):
        return f'<ImportBatch {self.filename} - {self.rows_imported}/{self.row_count}>'

class AuditLog(db.Model):
    __tablename__ = 'audit_log'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    entity_type = db.Column(db.String(50), nullable=False)  # transaction, goal, category, category_rule
    entity_id = db.Column(db.Integer, nullable=False)
    action = db.Column(db.String(20), nullable=False)  # create, update, delete
    previous_value = db.Column(db.Text, nullable=True)  # JSON serialized
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    __table_args__ = (
        db.CheckConstraint("entity_type IN ('transaction', 'goal', 'category', 'category_rule')", name='ck_audit_entity_type'),
        db.CheckConstraint("action IN ('create', 'update', 'delete')", name='ck_audit_action'),
    )
    
    def __repr__(self):
        return f'<AuditLog {self.entity_type} {self.entity_id} {self.action}>'