import os
import boto3
import json
import logging
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler
from logging import Logger
from json_repair import repair_json
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

def invoke_claude_3_sonnet(prompt: str, inference_profile_arn: str, logger: Logger, max_tokens: int = 100000) -> str | None:
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
        logger.error("Error invoking Claude:")
        logger.error(e)
        return None

def get_system_prompt(task: str, dom: str) -> str:
    prompt = f"""
#info
Review the provided dom and perform the following task. 

#task
{task}

#dom
{dom}

#Output Format
{{
    "data": {{
        "task_id": "194f2173-fee6-45d1-86ba-d65c4d2bfd34",
        "response": "on the left side navigation menus, above the Kubernetes menu, hover on Administrator menu and click on Infrastructure submenu. ",
        "url": "",
        "type": "browser-use",
        "request": "dom",
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

def format_response(response: str, logger: Logger) -> json:
    if response is None: return response
    response.replace("```", "")
    response = repair_json(response)
    try:
        response = json.loads(response)
        logger.info(response)
    except Exception as e:
        logger.error(e)