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

MAIN_UPDATE_ARCHIVE = "update.tar.gz"
LB_INSTALL_ARCHIVE = "loadbalancer.tar.gz"
LB_UPDATE_ARCHIVE = "loadbalancer_update.tar.gz"

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


@app.route("/api/v1/check_updates", methods=["GET"])
@limiter.limit("10 per minute")
def check_updates():

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
        changelog = repo.get_changelog(
            f"https://raw.githubusercontent.com/{config["git_owner"]}/{config["git_repo"]}_Update/refs/heads/main/changelog.json"
        )
        url = f"https://github.com/{config["git_owner"]}/{config["git_repo"]}/releases/tag/{next_version}"

        if not next_version:
            return (
                jsonify({"status": "error", "message": "Updates not found"}),
                HTTPStatus.BAD_REQUEST,
            )

        return (
            jsonify({"version": next_version, "changelog": changelog, "url": url}),
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


@app.route("/api/v1/update", methods=["GET"])
@limiter.limit("10 per minute")
def get_update():
    """Get next release version"""
    try:
        version = request.args.get("version")
        file_type = request.args.get("file_type")

        if not version:
            return (
                jsonify(
                    {"status": "error", "message": "Version parameter is required"}
                ),
                HTTPStatus.BAD_REQUEST,
            )

        if not file_type:
            return (
                jsonify(
                    {"status": "error", "message": "File type parameter is required"}
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

        match file_type:
            case "main":
                update_file = MAIN_UPDATE_ARCHIVE
            case "lb":
                update_file = LB_INSTALL_ARCHIVE
            case "lb_update":
                update_file = LB_UPDATE_ARCHIVE
            case _:
                return (
                    jsonify(
                        {
                            "status": "error",
                            "message": "File type parameter is not valide",
                        }
                    ),
                    HTTPStatus.BAD_REQUEST,
                )

        next_version = repo.get_next_version(version)
        upd_archive_url = f"https://github.com/{config["git_owner"]}/{config["git_repo"]}/releases/download/{next_version}/{update_file}"
        hash_md5 = repo.get_asset_hash(next_version, update_file)

        if not next_version:
            return (
                jsonify({"status": "error", "message": "Updates not found"}),
                HTTPStatus.BAD_REQUEST,
            )

        return (
            jsonify(
                {
                    "url": upd_archive_url,
                    "md5": hash_md5,
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


if __name__ == "__main__":
    DEFAULT_CONFIG = {
        "host": "0.0.0.0",
        "port": 8080,
        "debug": False,
        "git_owner": "Vateron-Media",
        "git_repo": "XC_VM",
    }

    # Load configuration
    config = Common.load_config(
        default_config=DEFAULT_CONFIG,
        config_file_path="config.ini",
        env_prefix="XC_VM_API_",
    )

    # Validate configuration
    required_keys = ["git_owner", "git_repo"]
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
