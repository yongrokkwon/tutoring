import os
import sys

from flask import Flask


def create_app() -> Flask:
    app = Flask(__name__)
    secret = os.environ.get("KW_NOTICE_SECRET_KEY")
    if not secret:
        print("WARNING: KW_NOTICE_SECRET_KEY not set, using dev fallback",
              file=sys.stderr)
        secret = "dev-secret-key"
    app.secret_key = secret

    from .routes import notices, preview, settings
    app.register_blueprint(notices.bp)
    app.register_blueprint(preview.bp)
    app.register_blueprint(settings.bp)

    return app
