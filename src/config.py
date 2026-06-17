"""Application configuration."""
import os

PORT = int(os.environ.get('PORT', 5000))
SECRET_KEY = os.environ.get('SECRET_KEY', 'change-this-in-production')
FLASK_ENV = os.environ.get('FLASK_ENV', 'production')
