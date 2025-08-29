# XC_VM Update API

---

## 📌 Overview
The XC_VM Update API is a Flask-based RESTful API for managing software updates for the XC_VM application. It interacts with the GitHub Releases API to provide information about available updates. The API is secure and rate-limited.
---

## ⚙️ Features
- 📦 Fetches the next release version, changelog, download URL, and MD5 hash from GitHub
- 🔒 Includes security headers for enhanced protection
- 🚦 Rate limiting to prevent abuse
- ⚙️ Flexible configuration via environment variables, config files, or command-line arguments
- ⏱️ Caches GitHub API responses for efficiency
- 🛠️ Comprehensive error handling and logging

---

## 🧠 Security and API architecture

At this stage, this API is used **as a support tool** and is not a mandatory part of the XC_VM panel. It is designed for:

- automating the retrieval of information about new releases from GitHub;
- secure processing and delivery of error logs to Telegram.

We are aware that using an external API server can pose a security threat — an attacker may attempt to spoof updates or collect data. Therefore, the architecture is based on the following principles:

- **No updates are installed directly through the API**. The user decides whether to download them or not.
- **The main source of truth is GitHub Releases**, not a third-party server.
- **An API error or unavailability does not affect the functionality of the panel**.
- In the future, the logging system will be redesigned: **error logs will be stored locally**, and the user will be able to send them manually via GitHub Issues or Telegram.
- The API itself will remain as a separate module or will be disabled in the final version if it is not needed.

---

## 🚀 Deployment

### Prerequisites
- Python 3.8+
- A GitHub repository with releases (e.g., `Vateron-Media/XC_VM`)
- A Telegram bot token (create via [@BotFather](https://core.telegram.org/bots#6-botfather))
- A Telegram chat ID (find via [@userinfobot](https://t.me/userinfobot))
- Optional: A GitHub API token for authenticated requests (to avoid rate limits)


### Environment Variables
| Variable | Description | Example |
|----------|-------------|---------|
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
   export XC_VM_API_GIT_OWNER="Vateron-Media"
   export XC_VM_API_GIT_REPO="XC_VM"
   ```
4. Run the API:
   ```bash
   python api.py
   ```
   Or use command-line arguments:
   ```bash
   python api.py --git_owner Vateron-Media --git_repo XC_VM
   ```

### Testing
Test the update endpoint:
```bash
curl "http://localhost:8080/api/v1/update?version=1.0.0"
```
Test the check_updates endpoint:
```bash
curl "http://localhost:8080/api/v1/check_updates?version=1.0.0"   
```

---

## 🌐 API Endpoints

### GET /api/v1/check_updates
Check for updates with the return of the next release version, change log, and release link

#### Request
- **Method**: GET
- **URL**: `/api/v1/check_updates?version=<version>`
- **Query Parameters**:
  - `version` (required): Current version in `X.Y.Z` format (e.g., `1.0.0`).

#### Response
- **Success (200 OK)**:
  ```json
  {
    "changelog": [
      {
        "changes": [
          "Initial release"
        ],
        "version": "1.0.0"
      },
      {
        "changes": [
          "Fixed authentication bug"
        ],
        "version": "1.0.1"
      }
    ],
    "url": "https://github.com/Vateron-Media/XC_VM/releases/tag/1.0.1",
    "version": "1.0.1"
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
curl "http://localhost:8080/api/v1/check_updates?version=1.0.0"
```


### GET /api/v1/update
Gets the download URL for `update.tar.gz` and its MD5 hash.

#### Request
- **Method**: GET
- **URL**: `/api/v1/update?version=<version>`
- **Query Parameters**:
  - `version` (required): Current version in `X.Y.Z` format (e.g., `1.0.0`).

#### Response
- **Success (200 OK)**:
  ```json
  {
      "url": "https://github.com/Vateron-Media/XC_VM/releases/download/1.0.1/update.tar.gz",
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
curl "http://localhost:8080/api/v1/update?version=1.0.0"
```

---

## 🛠️ Troubleshooting
1. **Test locally**:
   ```bash
   python api.py --git_owner Vateron-Media --git_repo XC_VM
   ```
2. **GitHub API rate limits**:
   - Provide a GitHub API token via `XC_VM_API_GIT_TOKEN` to increase rate limits.
3. **Invalid version format**:
   - Ensure versions follow the `X.Y.Z` format (e.g., `1.0.0`).

---

## 📋 Rate Limiting
- **GET /api/v1/releases**: 10 requests per minute
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
