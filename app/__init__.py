import os
from flask import Flask
from dotenv import load_dotenv

def create_app():
    load_dotenv()
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", "local-demo-change-me"),
        HOST=os.getenv("HOST", "127.0.0.1"),
        PORT=int(os.getenv("PORT", "5000")),
        DEBUG=os.getenv("FLASK_DEBUG", "false").lower() == "true",
    )
    from app.routes import bp
    app.register_blueprint(bp)
    return app
