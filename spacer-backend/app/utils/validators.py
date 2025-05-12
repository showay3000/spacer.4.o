import re
from datetime import datetime, timezone

def validate_email(email):
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_password(password):
    """Validate password strength."""
    # At least 8 characters, contains letters and numbers
    if len(password) < 8:
        return False
    if not re.search(r'[A-Za-z]', password):
        return False
    if not re.search(r'\d', password):
        return False
    return True

def validate_booking_dates(start_time, end_time):
    """Validate booking dates."""
    try:
        start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        end = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        
        # Ensure all datetimes are timezone-aware
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        # Check if dates are in the future
        if start < now:
            return False, "Start time must be in the future"
        
        # Check if end time is after start time
        if end <= start:
            return False, "End time must be after start time"
        
        # Check if booking duration is reasonable (e.g., not more than 24 hours)
        duration = end - start
        if duration.total_seconds() > 24 * 3600:
            return False, "Booking duration cannot exceed 24 hours"
        
        return True, None
    except ValueError:
        return False, "Invalid date format"

def validate_space_data(data):
    """Validate space creation/update data."""
    required_fields = ['name', 'description', 'address', 'city', 'price_per_hour', 'capacity']
    for field in required_fields:
        if field not in data:
            return False, f"{field} is required"
    
    # Validate price
    try:
        price = float(data['price_per_hour'])
        if price <= 0:
            return False, "Price must be greater than 0"
    except ValueError:
        return False, "Invalid price format"
    
    # Validate capacity
    try:
        capacity = int(data['capacity'])
        if capacity <= 0:
            return False, "Capacity must be greater than 0"
    except ValueError:
        return False, "Invalid capacity format"
    
    return True, None 