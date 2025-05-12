from app import create_app, db
from app.models.user import User
from app.models.space import Space, SpaceImage, SpaceAmenity
from app.models.booking import Booking, Payment
from app.models.testimonial import Testimonial

app = create_app()
with app.app_context():
    db.drop_all()  # Drop all tables to ensure a clean slate
    db.create_all()
    print("Database tables created successfully!") 