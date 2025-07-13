### README: Flask Error Logger for Heroku

---

## 📌 Overview
This Flask application receives error reports via HTTP POST, formats them into structured JSON, and sends the reports to a Telegram chat. Designed for easy deployment on Heroku with minimal configuration.

---

## ⚙️ Features
- 📤 Receives error reports via POST requests
- 🧩 Structures raw error data into readable JSON
- 📤 Sends formatted reports to Telegram as files
- ⏱️ Automatic timestamping and unique filenames
- 🔒 Secure configuration via environment variables
- 🚦 Comprehensive error handling

---

## 🚀 Heroku Deployment

### Prerequisites
1. Heroku account (free tier available)
2. Telegram bot token ([create one via @BotFather](https://core.telegram.org/bots#6-botfather))
3. Telegram chat ID (use @userinfobot to find yours)

### Deployment Steps
```bash
# Clone repository
git clone https://github.com/yourusername/flask-error-logger.git
cd flask-error-logger

# Create Heroku app
heroku create your-app-name

# Set configuration variables
heroku config:set TELEGRAM_TOKEN="your_bot_token"
heroku config:set TELEGRAM_CHAT_ID="your_chat_id"

# Deploy to Heroku
git push heroku main

# Verify deployment
heroku open
```

### Environment Variables
| Variable | Description | Example |
|----------|-------------|---------|
| `TELEGRAM_TOKEN` | Telegram bot token | `6849849849:AAFMdmsdrftgykOnrO8v2uTwwg3i8zKZlTI` |
| `TELEGRAM_CHAT_ID` | Target chat ID | `10077994977` |
| `PORT` | Server port (auto-set by Heroku) | `5000` |

---

## 🖥️ Local Development

### Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate    # Windows

# Install dependencies
pip install -r requirements.txt

# Run with environment variables
export TELEGRAM_TOKEN="your_token"
export TELEGRAM_CHAT_ID="your_chat_id"
python app.py

# Or use command-line arguments
python app.py --token your_token --chat_id your_chat_id
```

### Testing
Send a test error report:
```bash
curl -X POST http://localhost:5000/logs \
  -F "errors[0][type]=test" \
  -F "errors[0][log_message]=Test error" \
  -F "errors[0][date]=$(date +%s)" \
  -F "version=1.0" \
  -F "revision=abc123"
```

---

## 🌐 Endpoint
- **URL**: `/logs`
- **Method**: `POST`
- **Content-Type**: `application/x-www-form-urlencoded`
- **Parameters**: 
  - `errors[N][field]` - Error data fields
  - `version` - Application version
  - `revision` - Code revision

---

## 📋 Response Format
Successful response:
```json
{
  "status": "success",
  "message": "Error report sent to Telegram",
  "filename": "errors_20230712_143022.json"
}
```

---

## 🛠️ Troubleshooting
1. **Missing configuration**:
   ```bash
   heroku config:set TELEGRAM_TOKEN=your_token
   heroku config:set TELEGRAM_CHAT_ID=your_chat_id
   ```
   
2. **Check logs**:
   ```bash
   heroku logs --tail
   ```

3. **Test locally**:
   ```bash
   python app.py --token test_token --chat_id test_chat
   ```

---

## 📄 License
MIT License - Free for personal and commercial use

---

## 🔧 Requirements
- Python 3.7+
- Packages:
  - Flask
  - requests
  - python-dotenv (for local development)