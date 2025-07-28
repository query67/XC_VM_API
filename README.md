# XC_VM Update API

---

## 📌 Overview
The XC_VM Update API is a Flask-based RESTful API designed to manage software updates for the XC_VM application and handle error reports. It interacts with the GitHub Releases API to provide information about available updates and sends structured error reports to a Telegram chat for monitoring. The API is secure, rate-limited, and suitable for deployment on platforms like Heroku.

---

## ⚙️ Features
- 📦 Fetches the next release version, changelog, download URL, and MD5 hash from GitHub
- 📤 Receives and formats error reports into structured JSON
- 📬 Sends error reports to a Telegram chat as JSON files
- 🔒 Includes security headers for enhanced protection
- 🚦 Rate limiting to prevent abuse
- ⚙️ Flexible configuration via environment variables, config files, or command-line arguments
- ⏱️ Caches GitHub API responses for efficiency
- 🛠️ Comprehensive error handling and logging

---

## 🚀 Deployment

### Prerequisites
- Python 3.8+
- A GitHub repository with releases (e.g., `Vateron-Media/XC_VM`)
- A Telegram bot token (create via [@BotFather](https://core.telegram.org/bots#6-botfather))
- A Telegram chat ID (find via [@userinfobot](https://t.me/userinfobot))
- Optional: A GitHub API token for authenticated requests (to avoid rate limits)

### Deployment Steps (Heroku Example)
1. Clone the repository:
   ```bash
   git clone https://github.com/Vateron-Media/XC_VM_Update.git
   cd XC_VM_Update
   ```
2. Create a Heroku app:
   ```bash
   heroku create your-app-name
   ```
3. Set environment variables:
   ```bash
   heroku config:set XC_VM_API_TG_TOKEN="your_bot_token"
   heroku config:set XC_VM_API_TG_CHAT="your_chat_id"
   heroku config:set XC_VM_API_GIT_OWNER="Vateron-Media"
   heroku config:set XC_VM_API_GIT_REPO="XC_VM"
   ```
4. Deploy to Heroku:
   ```bash
   git push heroku main
   ```
5. Verify deployment:
   ```bash
   heroku open
   ```

### Environment Variables
| Variable | Description | Example |
|----------|-------------|---------|
| `XC_VM_API_TG_TOKEN` | Telegram bot token | `6849849849:AAFMdmsdrftgykOnrO8v2uTwwg3i8zKZlTI` |
| `XC_VM_API_TG_CHAT` | Telegram chat ID | `10077994977` |
| `XC_VM_API_GIT_OWNER` | GitHub repository owner | `Vateron-Media` |
| `XC_VM_API_GIT_REPO` | GitHub repository name | `XC_VM` |
| `XC_VM_API_HOST` | Server host | `0.0.0.0` |
| `XC_VM_API_PORT` | Server port | `8080` |
| `XC_VM_API_DEBUG` | Debug mode | `False` |

### Configuration File (Optional)
Rename `example.ini` to `config.ini` file:
```ini
[DEFAULT]
HOST = 0.0.0.0
PORT = 8080
DEBUG = False
GIT_OWNER = Vateron-Media
GIT_REPO = XC_VM
TG_TOKEN = your-telegram-bot-token
TG_CHAT = your-telegram-chat-id
```

---

## 🖥️ Local Development

### Setup
1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```
2. Install dependencies:
   ```bash
   python -m pip install -r requirements.txt
   ```
3. Set environment variables:
   ```bash
   export XC_VM_API_TG_TOKEN="your_token"
   export XC_VM_API_TG_CHAT="your_chat_id"
   export XC_VM_API_GIT_OWNER="Vateron-Media"
   export XC_VM_API_GIT_REPO="XC_VM"
   ```
4. Run the API:
   ```bash
   python api.py
   ```
   Or use command-line arguments:
   ```bash
   python api.py --tg_token your_token --tg_chat your_chat_id --git_owner Vateron-Media --git_repo XC_VM
   ```

### Testing
Test the release endpoint:
```bash
curl "http://localhost:8080/api/v1/update?version=v1.0.0"
```

Test the error report endpoint:
```bash
curl -X POST http://localhost:8080/api/v1/report \
  -F "version=v1.0.0" \
  -F "errors[0][type]=RuntimeError" \
  -F "errors[0][log_message]=Database connection failed" \
  -F "errors[0][log_extra]=db.py" \
  -F "errors[0][line]=42" \
  -F "errors[0][date]=1697059200"
```

---

## 🌐 API Endpoints

### GET /api/v1/update
Gets the download URL for `update.tar.gz` and its MD5 hash.

#### Request
- **Method**: GET
- **URL**: `/api/v1/update?version=<version>`
- **Query Parameters**:
  - `version` (required): Current version in `vX.Y.Z` format (e.g., `v1.0.0`).

#### Response
- **Success (200 OK)**:
  ```json
  {
      "url": "https://github.com/Vateron-Media/XC_VM/releases/download/v1.0.1/update.tar.gz",
      "md5": "d41d8cd98f00b204e9800998ecf8427e"
  }
  ```
- **Error (400 Bad Request)**:
  ```json
  {
    "status": "error",
    "message": "Version parameter is required"
  }
  ```
  or
  ```json
  {
    "status": "error",
    "message": "Invalid version format"
  }
  ```
- **Error (500 Internal Server Error)**:
  ```json
  {
    "status": "error",
    "message": "Internal server error",
    "error_type": "RequestException"
  }
  ```

#### Example
```bash
curl "http://localhost:8080/api/v1/releases?version=v1.0.0"
```

### POST /api/v1/report
Receives error reports via form data, formats them into a JSON document, and sends them to a Telegram chat as a file.

#### Request
- **Method**: POST
- **URL**: `/api/v1/report`
- **Content-Type**: `application/x-www-form-urlencoded`
- **Form Data**:
  - `version`: Application version (e.g., `v1.0.0`).
  - `errors[i][type]`: Error type (e.g., `RuntimeError`).
  - `errors[i][log_message]`: Error message.
  - `errors[i][log_extra]`: File where the error occurred.
  - `errors[i][line]`: Line number of the error.
  - `errors[i][date]`: Unix timestamp of the error.

#### Example Request
```bash
curl -X POST http://localhost:8080/api/v1/report \
  -F "version=v1.0.0" \
  -F "errors[0][type]=RuntimeError" \
  -F "errors[0][log_message]=Database connection failed" \
  -F "errors[0][log_extra]=db.py" \
  -F "errors[0][line]=42" \
  -F "errors[0][date]=1697059200" \
  -F "errors[1][type]=ValueError" \
  -F "errors[1][log_message]=Invalid input" \
  -F "errors[1][log_extra]=input.py" \
  -F "errors[1][line]=15" \
  -F "errors[1][date]=1697059210"
```

#### Formatted Output (Sent to Telegram)
```json
{
  "errors": [
    {
      "type": "RuntimeError",
      "message": "Database connection failed",
      "file": "db.py",
      "line": "42",
      "date": "1697059200",
      "human_date": "2023-10-11 20:00:00"
    },
    {
      "type": "ValueError",
      "message": "Invalid input",
      "file": "input.py",
      "line": "15",
      "date": "1697059210",
      "human_date": "2023-10-11 20:00:10"
    }
  ],
  "version": "v1.0.0",
  "received_at": "2025-07-27T08:37:00.123456+00:00"
}
```

#### Response
- **Success (200 OK)**:
  ```json
  {
    "status": "success",
    "message": "Error report sent successfully"
  }
  ```
- **Error (400 Bad Request)**:
  ```json
  {
    "status": "error",
    "message": "No form data received"
  }
  ```
  or
  ```json
  {
    "status": "error",
    "message": "Form data too large"
  }
  ```
- **Error (500 Internal Server Error)**:
  ```json
  {
    "status": "error",
    "message": "Telegram configuration missing"
  }
  ```
  or
  ```json
  {
    "status": "error",
    "message": "Failed to send report to Telegram",
    "telegram_response": "..."
  }
  ```

---

## 🛠️ Troubleshooting
1. **Missing configuration**:
   ```bash
   heroku config:set XC_VM_API_TG_TOKEN=your_token
   heroku config:set XC_VM_API_TG_CHAT=your_chat_id
   ```
2. **Check logs**:
   ```bash
   heroku logs --tail
   ```
3. **Test locally**:
   ```bash
   python api.py --tg_token test_token --tg_chat test_chat --git_owner Vateron-Media --git_repo XC_VM
   ```
4. **GitHub API rate limits**:
   - Provide a GitHub API token via `XC_VM_API_GIT_TOKEN` to increase rate limits.
5. **Invalid version format**:
   - Ensure versions follow the `vX.Y.Z` format (e.g., `v1.0.0`).

---

## 📋 Rate Limiting
- **GET /api/v1/releases**: 10 requests per minute
- **POST /api/v1/report**: 5 requests per minute
- Global: 200 requests per day, 50 requests per hour

Exceeding limits returns a 429 Too Many Requests response.

---

## 🔒 Security
The API includes the following security headers:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Content-Security-Policy: default-src 'self'`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`

---

## 📄 License
This project is licensed under the [AGPL-3.0 License](LICENSE).

---

## 🔧 Requirements
- Python 3.8+
- Packages:
  - Flask
  - Flask-Limiter
  - requests
  - gunicorn (for production)
  - configparser
  - argparse