from app.extensions import db
from datetime import datetime
import bcrypt

class User(db.Model):
    __tablename__ = 'users'
    
    VALID_ROLES = ['admin', 'owner', 'client']
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    _role = db.Column('role', db.String(20), nullable=False, default='client')
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    phone = db.Column(db.String(20))
    bio = db.Column(db.Text)
    avatar_url = db.Column(db.String(255))
    
    # Relationships
    spaces = db.relationship('Space', backref='owner', lazy=True)
    bookings = db.relationship('Booking', backref='user', lazy=True)
    
    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if 'role' in kwargs:
            self.role = kwargs['role']
        elif not hasattr(self, '_role') or not self._role:
            self.role = 'client'
    
    @property
    def role(self):
        return self._role.lower() if self._role else 'client'
    
    @role.setter
    def role(self, value):
        if isinstance(value, str):
            value = value.lower()
            if value not in self.VALID_ROLES:
                raise ValueError(f'Invalid role. Must be one of: {", ".join(self.VALID_ROLES)}')
            self._role = value
    
    def set_password(self, password):
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    @property
    def is_admin(self):
        return self.role == 'admin'
    
    @property
    def is_owner(self):
        return self.role == 'owner'
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'name': f'{self.first_name} {self.last_name}',
            'role': self.role,
            'phone': self.phone,
            'bio': self.bio,
            'avatar_url': self.avatar_url,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        } 