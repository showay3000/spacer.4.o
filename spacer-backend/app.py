from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from datetime import timedelta
import os
from app import create_app, db

app = create_app()

if __name__ == '__main__':
    app.run()

# ... existing code ... 