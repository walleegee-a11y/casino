"""Flask application factory for Hawkeye Web Server"""

import os
from flask import Flask
from hawkeye_web_server.config import Config


def create_app(config_class=Config):
    """Create and configure the Flask application"""

    # Create Flask app with correct template and static folders
    app = Flask(
        __name__,
        template_folder=Config.TEMPLATE_FOLDER,
        static_folder=Config.STATIC_FOLDER,
        static_url_path='/static'
    )

    # Load configuration
    app.config.from_object(config_class)

    # Set secret key for sessions
    app.secret_key = config_class.SECRET_KEY

    # Initialize config
    config_class.init_app(app)

    # Register blueprints
    from hawkeye_web_server.routes import api_bp, views_bp

    app.register_blueprint(views_bp)
    app.register_blueprint(api_bp, url_prefix='/api')

    # Log startup info
    print(f"[+] Flask app created")
    print(f"[+] Template folder: {Config.TEMPLATE_FOLDER}")
    print(f"[+] Static folder: {Config.STATIC_FOLDER}")
    print(f"[+] Blueprints registered")

    return app
