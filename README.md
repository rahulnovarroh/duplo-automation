# 🧠 Browser Automation Actions via Claude 3 + AWS Bedrock

This project allows you to automate web-based actions by sending DOM snapshots and task instructions to [Anthropic Claude 3 Sonnet](https://docs.aws.amazon.com/bedrock/latest/userguide/what-is-bedrock.html) through AWS Bedrock. It extracts actionable steps (like clicks) in structured JSON format.

---

## 📁 Project Structure

```
├── index.py              # Main entrypoint
├── utils.py              # Helper methods for logging, prompt building, model invocation
├── input_dom.txt         # HTML DOM snapshot input
├── .env                  # Environment variables (inference profile, log level, etc.)
├── logs/                 # Log files (e.g., server.log)
├── requirements.txt      # Python dependencies
└── README.md             # You're reading this 😉
```

---

## ⚙️ Setup

### 1. Clone the Repository

```bash
git clone git@github.com:rahulnovarroh/duplo-automation.git
cd duplo-automation
```

### 2. Create a Virtual Environment (optional but recommended)

```bash
python3 -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 📄 Environment Variables

Create a `.env` file in the root directory:

```
INFERENCE_PROFILE_ARN=your-anthropic-inference-profile-arn
LOG_LEVEL=INFO
LOG_DIR=logs
MAX_TOKENS=100000
```

---

## 🚀 Run the Script

Make sure `input_dom.txt` contains the DOM to process, then:

```bash
python index.py
```

Logs will be saved to `logs/server.log` and printed in the console.

---

## 📄 Example Output (JSON)

```json
{
  "data": {
    "task_id": "194f2173-fee6-45d1-86ba-d65c4d2bfd34",
    "response": "click on Infrastructure",
    "url": "",
    "type": "browser-use",
    "request": "dom",
    "actions": [
      {
        "selector": "html > body > app-root > vertical-layout > core-sidebar > app-menu > vertical-menu > div > div:nth-of-type(2) > ul > li > div > a",
        "action": "click",
        "waitBefore": 1000,
        "waitAfter": 1000
      }
    ]
  }
}
```

---

## 🧪 Tips for Devs

- Want to **stream live logs**?

  ```bash
  tail -f logs/server.log
  ```

- Ensure the DOM you input is **complete HTML** for best results.

---

## 📬 Issues or Feature Requests?

Feel free to open an [Issue](https://github.com/your-username/your-repo/issues) or [Pull Request](https://github.com/your-username/your-repo/pulls). Contributions welcome!

---

## 🧠 Powered By

- AWS Bedrock (Claude 3 Sonnet)
- Python + Boto3
- dotenv + logging + json-repair
