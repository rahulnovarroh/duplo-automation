import os
import time
import random
import boto3
import json
import logging
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler
from logging import Logger
load_dotenv()

def get_logging_config() -> Logger:
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_DIR = os.getenv("LOG_DIR", "logs")
    os.makedirs(LOG_DIR, exist_ok=True)
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format="%(asctime)s [%(levelname)s] [%(name)s] [%(process)d] %(message)s",
        handlers=[
            logging.StreamHandler(),
            RotatingFileHandler(
                f"{LOG_DIR}/server.log",
                maxBytes=10485760,  # 10MB
                backupCount=10
            )
        ]
    )

    return logging.getLogger(__name__)

def invoke_claude_3_sonnet(prompt: str, inference_profile_arn: str, logger: Logger, max_tokens: int = 90000) -> str | None:
    bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')
    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]
    }
    request_body_json = json.dumps(request_body)
    
    max_retries = os.getenv("MAX_THROTTLING_RETRIES", 5)
    retry_count = 0
    base_delay = os.getenv("BASE_THROTTLING_DELAY", 5)  # Base delay in seconds
    
    while retry_count < max_retries:
        try:
            response = bedrock_runtime.invoke_model(
                modelId=inference_profile_arn,
                body=request_body_json
            )

            response_body = json.loads(response["body"].read())
            if "content" in response_body and len(response_body["content"]) > 0:
                for content_item in response_body["content"]:
                    if content_item["type"] == "text":
                        return content_item["text"]
            
            return None
        except Exception as e:
            if "ThrottlingException" in str(e):
                retry_count += 1
                if retry_count >= max_retries:
                    logger.error(f"Maximum retries exceeded: {e}")
                    return str(e)
                
                # Calculate delay with exponential backoff and jitter
                delay = base_delay * (2 ** (retry_count - 1)) + random.uniform(0, 1)
                logger.warning(f"Rate limited. Retrying in {delay:.2f} seconds... (Attempt {retry_count}/{max_retries})")
                time.sleep(delay)
            else:
                logger.error("Error invoking Claude:")
                logger.error(e)
                return str(e)

def get_system_prompt(task: str, dom: str) -> str:
    prompt = f"""
#info
Review the provided dom and perform the following task. If the task is just a question then provide the relevant response. If possible, ask relevant question to the user to continue the chat.

#task
{task}

#dom
{dom}

#Output Format
{{
    "data": {{
        "response": "on the left side navigation menus, above the Kubernetes menu, hover on Administrator menu and click on Infrastructure submenu. ",
        "actions": [
            {{
                "selector": "html > body > app-root > vertical-layout > core-sidebar > app-menu > vertical-menu > div > div:nth-of-type(2) > ul > li > div > a",
                "action": "click",
                "waitBefore": 1000,
                "waitAfter": 1000
            }},
        ]
}}

#Important things in the output format - 
- DO NOT OUTPUT ANYTHING EXCEPT JSON RESULT
- selector should be the xpath starting from the root tag STRICTLY in the format: html > body > app-root > vertical-layout > core-sidebar > app-menu > vertical-menu > div > div:nth-of-type(2) > ul > li:nth-of-type(1) > div > a

"""
    return prompt
