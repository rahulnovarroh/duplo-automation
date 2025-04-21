import os
from dotenv import load_dotenv
from logging import Logger
from utils import (
    invoke_bedrock_model,
    invoke_openai_gpt4o,
    invoke_claude_37_sonnet,
    get_system_prompt,
    get_logging_config
)
from flask import Flask, request

app = Flask(__name__)

load_dotenv()
INFERENCE_PROFILE_ARN = os.getenv("INFERENCE_PROFILE_ARN")
MAX_TOKENS = os.getenv("MAX_TOKENS", 100000)

logger: Logger = get_logging_config()

def init_request(task: str, dom: str, logger: Logger, version: str='bedrock') -> str | None:
    if not dom or not task: return None
    if version == 'openai': return invoke_openai_gpt4o(get_system_prompt(task, dom), logger)
    if version == 'claude': return invoke_claude_37_sonnet(get_system_prompt(task, dom), logger)
    return invoke_bedrock_model(get_system_prompt(task, dom), INFERENCE_PROFILE_ARN, logger)

@app.route('/bedrock-agents', methods=['POST'])
def bedrock_agents():
    task = request.form["task"]
    dom = request.form["dom"]
    response = init_request(task, dom, logger)
    logger.info("------------------------------------------------------------------------------")
    logger.info(response)
    return response

@app.route('/openai-agents', methods=['POST'])
def openai_agents():
    task = request.form["task"]
    dom = request.form["dom"]
    response = init_request(task, dom, logger, 'openai')
    logger.info("------------------------------------------------------------------------------")
    logger.info(response)
    return response

@app.route('/claude-agents', methods=['POST'])
def claude_agents():
    task = request.form["task"]
    dom = request.form["dom"]
    response = init_request(task, dom, logger, 'claude')
    logger.info("------------------------------------------------------------------------------")
    logger.info(response)
    return response
