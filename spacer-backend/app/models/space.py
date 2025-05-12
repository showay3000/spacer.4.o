from app import db
from datetime import datetime

class SpaceAmenity(db.Model):
    __tablename__ = 'space_amenities'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    space_id = db.Column(db.Integer, db.ForeignKey('spaces.id', ondelete='CASCADE'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'space_id': self.space_id
        }

class SpaceReview(db.Model):
    __tablename__ = 'space_reviews'

    id = db.Column(db.Integer, primary_key=True)
    space_id = db.Column(db.Integer, db.ForeignKey('spaces.id', ondelete='CASCADE'), nullable=False)
    user_name = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'space_id': self.space_id,
            'user_name': self.user_name,
            'rating': self.rating,
            'comment': self.comment,
            'created_at': self.created_at.isoformat()
        }

class Space(db.Model):
    __tablename__ = 'spaces'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    address = db.Column(db.String(200), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    price_per_hour = db.Column(db.Float, nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    images = db.relationship('SpaceImage', backref='space', lazy=True, cascade='all, delete-orphan')
    bookings = db.relationship('Booking', backref='space', lazy=True, cascade='all, delete-orphan')
    amenities = db.relationship('SpaceAmenity', backref='space', lazy=True, cascade='all, delete-orphan', passive_deletes=True)
    reviews = db.relationship('SpaceReview', backref='space', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        try:
            images_list = [image.to_dict() for image in self.images] if self.images else []
        except Exception as e:
            images_list = []
            
        try:
            amenities_list = []
            if hasattr(self, 'amenities') and self.amenities is not None:
                for amenity in self.amenities:
                    try:
                        amenities_list.append(amenity.to_dict())
                    except Exception:
                        pass
        except Exception:
            amenities_list = []
            
        try:
            reviews_list = []
            if hasattr(self, 'reviews') and self.reviews is not None:
                for review in self.reviews:
                    try:
                        reviews_list.append(review.to_dict())
                    except Exception:
                        pass
        except Exception:
            reviews_list = []
            
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'address': self.address,
            'city': self.city,
            'price_per_hour': self.price_per_hour,
            'capacity': self.capacity,
            'owner_id': self.owner_id,
            'is_available': self.is_available,
            'images': images_list,
            'amenities': amenities_list,
            'reviews': reviews_list,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class SpaceImage(db.Model):
    __tablename__ = 'space_images'
    
    id = db.Column(db.Integer, primary_key=True)
    space_id = db.Column(db.Integer, db.ForeignKey('spaces.id', ondelete='CASCADE'), nullable=False)
    image_url = db.Column(db.String(255), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'space_id': self.space_id,
            'image_url': self.image_url,
            'is_primary': self.is_primary,
            'created_at': self.created_at.isoformat()
        }
