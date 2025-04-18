import os
from dotenv import load_dotenv
from logging import Logger
from utils import (
    format_response,
    invoke_claude_3_sonnet,
    get_system_prompt,
    get_logging_config
)
load_dotenv()
INFERENCE_PROFILE_ARN = os.getenv("INFERENCE_PROFILE_ARN")
MAX_TOKENS = os.getenv("MAX_TOKENS", 100000)

logger: Logger = get_logging_config()

def init_request(task: str, dom: str, logger: Logger) -> str | None:
    return invoke_claude_3_sonnet(get_system_prompt(task, dom), INFERENCE_PROFILE_ARN, logger)

task = """
Fill the following information in the form:
        Name: test
        VPC CIDR: 10.10.0.0/16
        Click on Create. 
"""

# Open the file in read mode
with open('input_dom.txt', 'r') as file:
    dom = file.read()

response = init_request(task, dom, logger)
logger.info("------------------------------------------------------------------------------")
logger.info(response)
