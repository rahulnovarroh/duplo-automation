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
                return response.choices[0].message.content
            
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
Review the provided DOM and perform the following task. If the task is just a question then provide the relevant response. If possible, ask relevant question to the user to continue the chat.

#task
{task}

#dom
{dom}

#STRICT OUTPUT FORMAT - DO NOT BREAK THIS FORMAT
Return ONLY a valid JSON object in the format below. DO NOT return any explanations, markdown, or text before or after the JSON. Your response MUST strictly match this structure:

{{
    "data": {{
        "response": "<Plain instruction in English, describing how to perform the task in a sentence or two. Be clear and brief.>",
        "actions": [
            {{
                "selector": "<Full XPath starting with html > body ...>" it has to be the complete path without ...,
                "fieldName": "<name of the field>",
                "description": "<Describe what are you doing in this field>",
                "action": "<click | hover | input | etc.>",
                "waitBefore": <number in ms>,
                "waitAfter": <number in ms>
            }}
        ]
    }}
}}

#IMPORTANT RULES
- Do NOT add any extra fields.
- selector MUST follow this strict format: html > body > app-root > ...
- waitBefore and waitAfter must be integers.
- NEVER return Markdown, text, or code blocks—just raw JSON.
- actions should ONLY be filled if I ask you to do anything on the dom

#FAIL IF BROKEN
Your output will be invalid unless it strictly follows this format. No wrapping in code blocks. No explanations. Just a JSON object.

"""
    return prompt
