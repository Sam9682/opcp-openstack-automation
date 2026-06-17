"""Flask application factory."""
import os
from flask import Flask, send_from_directory, redirect


def create_app():
    """Create and configure the Flask application."""
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'),
        static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates', 'assets')
    )

    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'change-this-in-production')

    # Health check endpoint
    @app.route('/health')
    def health():
        return {'status': 'healthy'}, 200

    # Serve the skillhub website
    @app.route('/')
    def index():
        return send_from_directory(app.template_folder, 'index.html')

    @app.route('/<path:filepath>')
    def serve_file(filepath):
        return send_from_directory(app.template_folder, filepath)

    return app
