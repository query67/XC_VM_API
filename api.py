import requests
from datetime import datetime, timezone
from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
from http import HTTPStatus
from helpers.git_releases import GitHubReleases
import helpers.common as Common

app = Flask(__name__)

UPDATE_ARCHIVE_NAME = "update.tar.gz"
CHANGELOG_FILE_URL = "https://raw.githubusercontent.com/Vateron-Media/XC_VM_Update/refs/heads/main/changelog.json"

# Rate limiting setup
limiter = Limiter(
    app=app, key_func=get_remote_address, default_limits=["200 per day", "50 per hour"]
)


# Security headers middleware
@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"
    )
    return response


@app.route("/api/v1/update", methods=["GET"])
@limiter.limit("10 per minute")
def get_release():
    """Get next release version"""
    try:
        version = request.args.get("version")
        if not version:
            return (
                jsonify(
                    {"status": "error", "message": "Version parameter is required"}
                ),
                HTTPStatus.BAD_REQUEST,
            )

        # Sanitize input
        version = version.strip()
        if not repo.is_valid_version(version):
            return (
                jsonify({"status": "error", "message": "Invalid version format"}),
                HTTPStatus.BAD_REQUEST,
            )

        next_version = repo.get_next_version(version)
        upd_archive_url = f"https://github.com/{config["git_owner"]}/{config["git_repo"]}/releases/download/{next_version}/{UPDATE_ARCHIVE_NAME}"
        hash_md5 = repo.get_asset_hash(next_version, UPDATE_ARCHIVE_NAME)

        if not next_version:
            return (
                jsonify({"status": "error", "message": "Updates not found"}),
                HTTPStatus.BAD_REQUEST,
            )

        return (
            jsonify(
                {
                    "status": "success",
                    "data": {
                        "url": upd_archive_url,
                        "md5": hash_md5,
                    },
                }
            ),
            HTTPStatus.OK,
        )

    except ValueError as ve:
        return (
            jsonify({"status": "error", "message": f"Invalid version: {str(ve)}"}),
            HTTPStatus.BAD_REQUEST,
        )
    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Internal server error",
                    "error_type": type(e).__name__,
                }
            ),
            HTTPStatus.INTERNAL_SERVER_ERROR,
        )


@app.route("/api/v1/report", methods=["POST"])
@limiter.limit("5 per minute")
def report():
    """Handle incoming error reports"""
    try:
        if not request.form:
            return (
                jsonify({"status": "error", "message": "No form data received"}),
                HTTPStatus.BAD_REQUEST,
            )

        # Validate form data size
        if len(request.form) > 1000:  # Adjust limit as needed
            return (
                jsonify({"status": "error", "message": "Form data too large"}),
                HTTPStatus.BAD_REQUEST,
            )

        # Format error data
        formatted_data = Common.format_errors(request.form)

        # Generate filename with timestamp
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"errors_{timestamp}.json"

        # Validate Telegram configuration
        if not config.get("tg_token") or not config.get("tg_chat"):
            return (
                jsonify(
                    {"status": "error", "message": "Telegram configuration missing"}
                ),
                HTTPStatus.INTERNAL_SERVER_ERROR,
            )

        # Send file to Telegram with timeout
        url = f"https://api.telegram.org/bot{config['tg_token']}/sendDocument"
        response = requests.post(
            url,
            data={"chat_id": config["tg_chat"]},
            files={"document": (filename, formatted_data.encode("utf-8"))},
            timeout=10,
        )

        if response.status_code != 200:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Failed to send report to Telegram",
                        "telegram_response": response.text,
                    }
                ),
                HTTPStatus.INTERNAL_SERVER_ERROR,
            )

        return (
            jsonify({"status": "success", "message": "Error report sent successfully"}),
            HTTPStatus.OK,
        )

    except requests.exceptions.RequestException as re:
        return (
            jsonify({"status": "error", "message": f"Network error: {str(re)}"}),
            HTTPStatus.INTERNAL_SERVER_ERROR,
        )
    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Internal server error",
                    "error_type": type(e).__name__,
                }
            ),
            HTTPStatus.INTERNAL_SERVER_ERROR,
        )


if __name__ == "__main__":
    DEFAULT_CONFIG = {
        "host": "0.0.0.0",
        "port": 8080,
        "debug": False,
        "git_owner": "Vateron-Media",
        "git_repo": "XC_VM",
        "tg_token": os.environ.get("TG_TOKEN", ""),
        "tg_chat": os.environ.get("TG_CHAT", ""),
    }

    # Load configuration
    config = Common.load_config(
        default_config=DEFAULT_CONFIG,
        config_file_path="config.ini",
        env_prefix="XC_VM_API_",
    )

    # Validate configuration
    required_keys = ["git_owner", "git_repo", "tg_token", "tg_chat"]
    missing_keys = [key for key in required_keys if not config.get(key)]
    if missing_keys:
        raise ValueError(f"Missing required configuration: {', '.join(missing_keys)}")

    repo = GitHubReleases(config["git_owner"], config["git_repo"])

    # Run with gunicorn in production
    if not config["debug"]:
        from gunicorn.app.base import Application

        class FlaskApplication(Application):
            def __init__(self, app):
                self.application = app
                super().__init__()

            def load_config(self):
                self.cfg.set("bind", f"{config['host']}:{config['port']}")
                self.cfg.set("workers", 4)
                self.cfg.set("timeout", 30)

            def load(self):
                return self.application

        FlaskApplication(app).run()
    else:
        app.run(host=config["host"], port=config["port"], debug=config["debug"])
