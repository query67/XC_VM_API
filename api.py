import os
import requests
import json
import argparse
from datetime import datetime, timezone
from flask import Flask, request, jsonify

app = Flask(__name__)

# Initialization with default values (empty strings)
TELEGRAM_TOKEN = ""
TELEGRAM_CHAT_ID = ""


def load_config():
    """
    Loads configuration from environment variables or command-line arguments.
    Priority: command-line arguments > environment variables > default values.
    """
    global TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Flask Error Logger")
    parser.add_argument("--token", type=str, help="Telegram Bot Token")
    parser.add_argument("--chat_id", type=str, help="Telegram Chat ID")
    args = parser.parse_args()

    # Set values (command-line arguments take precedence)
    TELEGRAM_TOKEN = args.token or os.getenv("TELEGRAM_TOKEN", "")
    TELEGRAM_CHAT_ID = args.chat_id or os.getenv("TELEGRAM_CHAT_ID", "")

    # Check required parameters
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        raise ValueError("Telegram token and chat ID must be provided")


# Load configuration on application startup
load_config()


def format_errors(data):
    """
    Formats received errors into a structured JSON document.
    Handles:
    - Multiple errors in a single report
    - Timestamp conversion
    - Missing fields
    """
    try:
        errors = []
        i = 0

        # Iterate through errors (format: errors[0][type], errors[1][type], ...)
        while True:
            prefix = f"errors[{i}]"
            if f"{prefix}[type]" not in data:
                break

            # Build a dictionary with error data (with key existence checks)
            error_data = {
                "type": data.get(f"{prefix}[type]", "unknown"),
                "message": data.get(f"{prefix}[log_message]", ""),
                "file": data.get(f"{prefix}[log_extra]", ""),
                "line": data.get(f"{prefix}[line]", "0"),
                "date": data.get(f"{prefix}[date]", "0"),
            }

            # Convert timestamp to human-readable format
            try:
                dt = datetime.utcfromtimestamp(int(error_data["date"]))
                error_data["human_date"] = dt.strftime("%Y-%m-%d %H:%M:%S")
            except (ValueError, TypeError):
                error_data["human_date"] = "invalid_timestamp"

            errors.append(error_data)
            i += 1

        # Build the final JSON
        return json.dumps(
            {
                "errors": errors,
                "version": data.get("version", ""),
                "revision": data.get("revision", ""),
                "received_at": datetime.now(timezone.utc).isoformat(),
            },
            indent=2,
            ensure_ascii=False,
        )

    except Exception as e:
        # Return raw data if formatting fails
        return f"Formatting error: {str(e)}\n\nRaw data:\n{json.dumps(dict(data), indent=2)}"


@app.route("/report", methods=["POST"])
def report():
    """Main handler for incoming error reports"""
    try:
        # Check if form data is present
        if not request.form:
            return jsonify({"status": "error", "message": "No form data received"}), 400

        # Format error data
        formatted_data = format_errors(request.form)

        # Generate filename with timestamp
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"errors_{timestamp}.json"

        # Send file to Telegram
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument"
        response = requests.post(
            url,
            data={"chat_id": TELEGRAM_CHAT_ID},
            files={"document": (filename, formatted_data.encode("utf-8"))},
            timeout=10,
        )

        # Handle Telegram API response
        if response.status_code != 200:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Telegram API error",
                        "telegram_response": response.text,
                    }
                ),
                500,
            )

        return jsonify(
            {
                "status": "success",
                "message": "Error report sent to Telegram",
                "filename": filename,
            }
        )

    except Exception as e:
        # Handle unexpected errors
        return (
            jsonify(
                {
                    "status": "critical_error",
                    "message": f"Internal server error: {str(e)}",
                    "error_type": type(e).__name__,
                }
            ),
            500,
        )


if __name__ == "__main__":
    # Run Flask app with configurable port
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
