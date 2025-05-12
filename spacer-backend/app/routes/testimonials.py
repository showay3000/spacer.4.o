from flask import Blueprint, jsonify
from app.models.testimonial import Testimonial
from app import db

testimonials_bp = Blueprint('testimonials', __name__)

# Sample testimonials data
SAMPLE_TESTIMONIALS = [
    {
        'name': 'Sarah Johnson',
        'role': 'Space Owner',
        'content': 'This platform has made managing my creative studio so much easier. The booking system is seamless and the support team is always helpful!',
        'rating': 5,
        'image_url': 'https://randomuser.me/api/portraits/women/1.jpg'
    },
    {
        'name': 'Michael Chen',
        'role': 'Regular Client',
        'content': 'I\'ve booked several meeting rooms through this platform. The spaces are always as described and the booking process is straightforward.',
        'rating': 5,
        'image_url': 'https://randomuser.me/api/portraits/men/2.jpg'
    },
    {
        'name': 'Emily Rodriguez',
        'role': 'Event Organizer',
        'content': 'The variety of spaces available is impressive. I\'ve found perfect venues for both small meetings and larger events.',
        'rating': 4,
        'image_url': 'https://randomuser.me/api/portraits/women/3.jpg'
    }
]

@testimonials_bp.route('', methods=['GET'])
@testimonials_bp.route('/', methods=['GET'])
def get_testimonials():
    """
    Get all testimonials
    ---
    tags:
      - Testimonials
    responses:
      200:
        description: List of testimonials
        content:
          application/json:
            schema:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                    example: 1
                  name:
                    type: string
                    example: "John Doe"
                  role:
                    type: string
                    example: "Space Owner"
                  content:
                    type: string
                    example: "Great experience using this platform!"
                  rating:
                    type: integer
                    example: 5
                  image_url:
                    type: string
                    example: "https://example.com/avatar.jpg"
    """
    # Check if we have any testimonials in the database
    if Testimonial.query.count() == 0:
        # Add sample testimonials if none exist
        for testimonial_data in SAMPLE_TESTIMONIALS:
            testimonial = Testimonial(**testimonial_data)
            db.session.add(testimonial)
        db.session.commit()
    
    testimonials = Testimonial.query.all()
    return jsonify([testimonial.to_dict() for testimonial in testimonials]), 200 