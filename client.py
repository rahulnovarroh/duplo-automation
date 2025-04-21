import json
import random
import gradio as gr
from gradio import ChatMessage
from server import init_request
from logging import Logger
from utils import (
    get_logging_config
)
logger: Logger = get_logging_config()
dom = ''
with open('input_dom.txt', 'r') as file:
    dom = file.read()

data_response = """
{
    "name": "Test"
}
"""

def chat(message, history):
    global data_response
    response = init_request(message, dom, logger, 'openai')
    print(response)
    if response is not None:
        response = response.replace("```json", "")
        response = response.replace("```", "")
        response_json = json.loads(response)
        data_response = response_json["data"]["response"]
        return data_response, gr.Code(language="json", value=json.dumps(response_json["data"]["actions"], indent=4))
    return "", gr.Code(language="json", value=json.dumps("[]", indent=4))
    

def random_response(message, history):
    response = init_request(message, dom, logger, 'openai')
    response_json_str = response
    print(response)
    response = response.replace("```json", "")
    response = response.replace("```", "")
    response = json.loads(response)
    print(response)
    data_response, data_actions = "", []
    if "data" in response and "response" in response["data"]:
        data_response = response["data"]["response"]

    if "data" in response and "actions" in response["data"]:
        data_actions = response["data"]["actions"]

    response = f"""
<strong>Response:</strong> {data_response}
<strong>Actions:</strong> 
"""
    return response + gr.JSON(data_actions)

# demo = gr.ChatInterface(chat, type="messages", autofocus=False)
# code = gr.Code(render=False)
# demo = gr.ChatInterface(
#                 chat,
#                 additional_outputs=[code],
#                 type="messages"
#             )
# code.render()

with gr.Blocks() as demo:
    code = gr.Code(render=False)
    with gr.Row():
        with gr.Column():
            gr.Markdown("<center><h1>Type your input here</h1></center>")
            gr.ChatInterface(
                chat,
                additional_outputs=[code],
                type="messages"
            )
        with gr.Column():
            gr.Markdown("<center><h1>Actions</h1></center>")
            code.render()

if __name__ == "__main__":
    demo.launch()
