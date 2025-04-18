# 🧠 Browser Automation with Claude 3 via AWS Bedrock

This project enables intelligent web UI automation using Claude 3 Sonnet via AWS Bedrock. It takes a DOM snapshot and a natural language task (even ambiguous), extracts relevant user intent, and returns a structured JSON of actions to perform in the browser.

---

## 📁 Project Structure

```
├── index.py              # Flask API that takes task + DOM and returns action JSON
├── utils.py              # Claude 3 invocation, retry logic, logging, prompt formatting
├── input_dom.txt         # Sample DOM input file
├── .env                  # Secrets and config (inference ARN, log level, etc.)
├── logs/                 # Logs directory for debugging
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
BASE_THROTTLING_DELAY=2
MAX_THROTTLING_RETRIES=5
```

---

## 🚀 Run the Flask Server

```bash
flask --app index run --debug
```

The server starts on `127.0.0.1:5000` and exposes a POST endpoint:

```curl --location 'http://127.0.0.1:5000/agents' \
--form 'dom="<vertical-layout _ngcontent-hie-c55=\"\"...."' \
--form 'task="No just provide default fields"
```

---

## 🔁 Multi-Turn Support & Dynamic Prompting

The system is designed to:

- Extract tasks from **ambiguous** natural language
- Ask follow-up questions if more info is needed
- Insert task + DOM into a system prompt dynamically
- Return precise UI actions in JSON format

**Example:**
> User: "how do I create an infra?"

> Claude: "You can create an infra by specifying VPC CIDR and other parameters. Would you like me to create one for you?"

> User: "Yes"

> Claude returns structured JSON of selectors + clicks + wait timing

User preferences like _"Do you want me to ask before committing changes?"_ can be layered in future iterations.

---

## 📄 Example Output

```json
{
  "data": {
    "response": "click on Infrastructure",
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

## 🧪 Dev Tips

- Tail logs live during testing:

```bash
tail -f logs/server.log
```

- Use Postman or `curl` to test POST requests with different DOMs and tasks.

- Structure your DOM input with full context for better action predictions.

---

## 🧠 Powered By

- AWS Bedrock + Claude 3 Sonnet
- Python + Flask + dotenv
- Logging, retries, and prompt engineering

