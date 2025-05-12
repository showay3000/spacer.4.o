# Spacer Backend

A platform connecting space owners with individuals seeking unique spaces for meetings, events, and activities.

## Features

- User Authentication (JWT)
- Space Management
- Booking System
- Payment Integration
- Email Notifications
- Image Upload (Cloudinary)

## Tech Stack

- Python (Flask)
- PostgreSQL
- JWT Authentication
- Sendinblue for Email
- Cloudinary for Image Upload

## Setup Instructions

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file with the following variables:
   ```
   DATABASE_URL=postgresql://username:password@localhost:5432/spacer_db
   JWT_SECRET_KEY=your_jwt_secret
   CLOUDINARY_CLOUD_NAME=your_cloud_name
   CLOUDINARY_API_KEY=your_api_key
   CLOUDINARY_API_SECRET=your_api_secret
   SENDINBLUE_API_KEY=your_sendinblue_key
   ```
5. Initialize the database:
   ```bash
   flask db init
   flask db migrate
   flask db upgrade
   ```
6. Run the application:
   ```bash
   flask run
   ```

## API Documentation

API documentation is available at `/api/docs` when running the application.

## Testing

Run tests using pytest:
```bash
pytest
```

## Project Structure

```
spacer/
├── app/
│   ├── __init__.py
│   ├── models/
│   ├── routes/
│   ├── schemas/
│   ├── services/
│   └── utils/
├── migrations/
├── tests/
├── .env
├── .gitignore
├── config.py
├── requirements.txt
└── run.py
```

# Spacer API Documentation

## Overview
Spacer is a space booking platform that allows users to list, discover, and book spaces for various purposes. The API provides endpoints for user management, space management, bookings, and payments.

## API Documentation
The API is documented using Swagger UI, which provides an interactive interface to explore and test the endpoints.

### Accessing Swagger UI
1. Start the backend server
2. Visit `http://localhost:5001/docs` in your browser
3. You can now browse all available endpoints, see their request/response schemas, and try them out

### Authentication
The API uses JWT (JSON Web Token) for authentication. Most endpoints require a valid access token in the Authorization header:
```
Authorization: Bearer <access_token>
```

To get an access token:
1. Register a new user using `/api/auth/register`
2. Login using `/api/auth/login` to receive access and refresh tokens

## Postman Collection
A Postman collection is provided for easy testing of the API endpoints.

### Importing the Collection
1. Open Postman
2. Click "Import" button
3. Select the `postman_collection.json` file from the project root
4. The collection will be imported with all endpoints and example requests

### Environment Setup
1. Create a new environment in Postman
2. Add the following variables:
   - `base_url`: `http://localhost:5001`
   - `access_token`: (leave empty, will be set after login)

### Using the Collection
1. Make sure the environment is selected
2. Start with the "Register User" request in the Authentication folder
3. Use the "Login" request to get an access token
4. The token will be automatically used for other requests that require authentication

## Available Endpoints

### Authentication
- `POST /api/auth/register` - Register a new user
- `POST /api/auth/login` - Login user
- `GET /api/auth/me` - Get current user profile

### Users
- `GET /api/users` - List all users (Admin only)
- `GET /api/users/profile` - Get current user profile
- `PUT /api/users/profile` - Update user profile
- `GET /api/users/activities` - Get user's activities

### Spaces
- `GET /api/spaces` - List all spaces
- `POST /api/spaces` - Create a new space (Owner/Admin)
- `PUT /api/spaces/:id` - Update a space
- `DELETE /api/spaces/:id` - Delete a space

### Bookings
- `GET /api/bookings` - List all bookings
- `GET /api/bookings/:id` - Get booking details
- `POST /api/bookings` - Create a new booking
- `POST /api/bookings/:id/cancel` - Cancel a booking

### Payments
- `POST /api/payments/mpesa/initiate/:booking_id` - Initiate M-Pesa payment

## Models

### User
```json
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "name": "John Doe",
  "role": "client",
  "phone": "254712345678",
  "bio": "Software developer",
  "avatar_url": "https://example.com/avatar.jpg",
  "is_verified": true,
  "created_at": "2024-03-20T12:00:00Z",
  "updated_at": "2024-03-20T12:00:00Z"
}
```

### Space
```json
{
  "id": 1,
  "name": "Conference Room",
  "description": "Spacious room for meetings",
  "address": "123 Main St",
  "city": "Nairobi",
  "price_per_hour": 100.0,
  "capacity": 20,
  "is_available": true,
  "owner_id": 1,
  "images": [
    {
      "id": 1,
      "image_url": "https://example.com/space.jpg",
      "is_primary": true
    }
  ],
  "created_at": "2024-03-20T12:00:00Z",
  "updated_at": "2024-03-20T12:00:00Z"
}
```

### Booking
```json
{
  "id": 1,
  "space_id": 1,
  "user_id": 1,
  "start_time": "2024-03-20T14:00:00Z",
  "end_time": "2024-03-20T16:00:00Z",
  "total_price": 200.0,
  "purpose": "Team meeting",
  "status": "pending",
  "payment_status": "pending",
  "created_at": "2024-03-20T12:00:00Z",
  "updated_at": "2024-03-20T12:00:00Z"
}
```

### Payment
```json
{
  "id": 1,
  "booking_id": 1,
  "amount": 200.0,
  "payment_method": "mpesa",
  "transaction_id": "MPESA123456789",
  "status": "completed",
  "created_at": "2024-03-20T12:00:00Z",
  "updated_at": "2024-03-20T12:00:00Z"
}
```

## Error Handling
The API uses standard HTTP status codes and returns error messages in a consistent format:
```json
{
  "error": "Error message here"
}
```

Common status codes:
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `500` - Internal Server Error 