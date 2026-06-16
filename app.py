"""Application entry point"""
import os
import sys

# Ensure the project root is on the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.app import create_app
from src.config import PORT

def main():
    """Main entry point"""
    # Create Flask app
    app = create_app()
    
    # Run application
    app.run(
        host='0.0.0.0', 
        port=PORT, 
        debug=os.environ.get('FLASK_ENV') == 'development'
    )

if __name__ == '__main__':
    main()
