import os
import time
import random
import boto3
import json
import logging
import anthropic
from anthropic import Anthropic
from openai import OpenAI
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

def invoke_bedrock_model(prompt: str, inference_profile_arn: str, logger: Logger, max_tokens: int = 130000) -> str | None:
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
    
    max_retries = int(os.getenv("MAX_THROTTLING_RETRIES", 5))
    retry_count = 0
    base_delay = int(os.getenv("BASE_THROTTLING_DELAY", 5))  # Base delay in seconds
    
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

def invoke_openai_gpt4o(prompt: str, logger: Logger, max_tokens: int = 4096) -> str | None:
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    request_body = {
        "model": os.getenv("OPENAI_MODEL"),
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": max_tokens
    }
    
    max_retries = int(os.getenv("MAX_THROTTLING_RETRIES", 5))
    retry_count = 0
    base_delay = int(os.getenv("BASE_THROTTLING_DELAY", 5))  # Base delay in seconds
    
    while retry_count < max_retries:
        try:
            response = openai_client.chat.completions.create(**request_body)
            
            if response.choices and len(response.choices) > 0:
                content: str = response.choices[0].message.content
                content = content.replace("```json", "")
                content = content.replace("```", "")
                return content
            
            return None
        except Exception as e:
            # OpenAI uses RateLimitError for throttling
            if "RateLimitError" in str(e) or "rate_limit" in str(e).lower():
                retry_count += 1
                if retry_count >= max_retries:
                    logger.error(f"Maximum retries exceeded: {e}")
                    return str(e)
                
                # Calculate delay with exponential backoff and jitter
                delay = base_delay * (2 ** (retry_count - 1)) + random.uniform(0, 1)
                logger.warning(f"Rate limited. Retrying in {delay:.2f} seconds... (Attempt {retry_count}/{max_retries})")
                time.sleep(delay)
            else:
                logger.error("Error invoking GPT-4o:")
                logger.error(e)
                return str(e)

def invoke_claude_37_sonnet(prompt: str, logger: Logger, max_tokens: int = 4096) -> str | None:
    # Initialize the Anthropic client
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    max_retries = int(os.getenv("MAX_THROTTLING_RETRIES", 5))
    retry_count = 0
    base_delay = int(os.getenv("BASE_THROTTLING_DELAY", 5))  # Base delay in seconds
    
    while retry_count < max_retries:
        try:
            # Create message using the Anthropic API
            response = client.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=max_tokens,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            # Extract the response text
            if response.content and len(response.content) > 0:
                for content_block in response.content:
                    if content_block.type == "text":
                        return content_block.text
            
            return None
        except Exception as e:
            # Anthropic uses rate limit errors similar to this pattern
            if "rate_limit" in str(e).lower() or "429" in str(e):
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
Carefully analyze the provided DOM to perform the given task. Your job is to simulate how a user would interact with the web UI based on what is visible in the DOM.

- If the task is a question, answer it based on the information available in the DOM.
- If the task is DevOps-related (e.g., launching an EC2 instance, managing infrastructure, etc.) on the Duplo website, extract all necessary UI selectors and steps to complete the operation using the DOM.
- If the DOM is missing required elements (like form fields, buttons, or modal dialogs), you MUST set "require_new_dom": true and clearly state what is missing.

#task
{task}

#dom
{dom}

#STRICT OUTPUT FORMAT - DO NOT BREAK THIS FORMAT
Return ONLY a valid JSON object in the format below. DO NOT return any explanations, markdown, or text before or after the JSON. Your response MUST strictly match this structure:

{{
    "data": {{
        "response": "<Plain English instruction on how to perform the task using available DOM.>",
        "actions": [
            {{
                "selector": "<Full XPath starting with html > body ...>",
                "fieldName": "<Name of the UI field or button>",
                "description": "<What this step is doing>",
                "action": "<click | hover | input | etc.>",
                "waitBefore": <number in ms>,
                "waitAfter": <number in ms>
            }}
        ],
        "require_new_dom": <true | false>,
        "new_dom_description": "<Explain what is missing and why the new DOM is needed. If require_new_dom=false, leave this empty string.>"
    }}
}}

#IMPORTANT RULES
- CRITICAL: You MUST include ALL required navigation steps, even when they involve multiple clicks through a navigation hierarchy.
- For multi-level navigation (e.g., clicking a dropdown then a submenu item), include SEPARATE action items for EACH click in the sequence.
- If a task requires clicking "Cloud Services" and then "Hosts", you MUST include both as separate action items.
- When navigation involves expanding a section and then clicking a link within it, BOTH actions must be included.
- Actions must be in the correct chronological order that a human would perform them.
- You must validate whether the DOM contains ALL the required UI elements to complete the task.
- If part of the workflow (e.g., a form to fill in EC2 instance details) is missing in the DOM, you MUST set require_new_dom to true and explain what's missing in new_dom_description.
- Do NOT add any extra fields to the JSON.
- selector MUST follow strict XPath starting with: html > body > app-root > ...
- NEVER return Markdown, text, or code blocks—just raw JSON.
- Only add steps in the "actions" array if the task involves interacting with the UI.

#FAIL IF BROKEN
Your output will be invalid unless it strictly follows the above format. No wrapping in code blocks. No explanations. Just a JSON object.

#COMPLETENESS CHECK 
Before returning your final response, verify that your actions array includes ALL navigation steps needed. Check if any intermediate clicks (such as expanding a menu section before clicking a link within it) are missing. If the task involves multi-level navigation, confirm that EACH level has its own action item.
"""
    return prompt
