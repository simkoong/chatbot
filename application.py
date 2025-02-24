from flask import Flask, render_template, request
import sys
from chatbot import Chatbot
from common import model, currTime
from characters import system_role, instruction
from concurrent.futures import ThreadPoolExecutor
import requests
import concurrent


# jjinchin 인스턴스 생성
jjinchin = Chatbot(
    model = model.basic,
    system_role = system_role,
    instruction = instruction
)


application = Flask(__name__)


@application.route("/")
def hello():
    return "Hello goorm!"


@application.route("/welcome")
def welcome():  # 함수명은 꼭 welcome일 필요는 없습니다.
    return "Hello goorm!"


@application.route("/chat-app")
def chat_app():
    return render_template("chat.html")


# 메아리 코드
# @application.route('/chat-api', methods=['POST'])
# def chat_api():
#     print("request.json:", request.json)
#     return {"response_message": "나도 " + request.json['request_message']}


@application.route('/chat-api', methods=['POST'])
def chat_api():
    request_message = request.json['request_message']
    print("request_message:", request_message)
    jjinchin.add_user_message(request_message)
    response = jjinchin.send_request()
    jjinchin.add_response(response)
    response_message = jjinchin.get_response_content()
    jjinchin.handle_token_limit(response)
    jjinchin.clean_context()
    print("response_message:", response_message)
    return {"response_message": response_message}


def format_response(resp, useCallback=False):
    data = {
            "version": "2.0",
            "useCallback": useCallback,
            "template": {
                "outputs": [
                    {
                        "simpleText": {
                            "text": resp
                        }
                    }
                ]
            }
        }
    return data


executor = ThreadPoolExecutor(max_workers=1)


# 비동기 호출 개선 후 코드
def async_send_request(chat_gpt, callbackUrl, future):
    # future가 완료될 때까지 대기. 이후는 개선 전 코드와 동일
    response = future.result()
    chat_gpt.add_response(response)
    response_message = chat_gpt.get_response_content()
    print("response_message:", response_message)
    chat_gpt.handle_token_limit(response)
    chat_gpt.clean_context()
    response_to_kakao = format_response(response_message, useCallback=False)
    callbackResponse = requests.post(callbackUrl, json=response_to_kakao)
    print("CallbackResponse:", callbackResponse.text)
    print(f"{'-'*50}\n{currTime()} requests.post 완료\n{'-'*50}")


@application.route('/chat-kakao', methods=['POST'])
def chat_kakao():
    print(f"{'-'*50}\n{currTime()} chat-kakao 시작\n{'-'*50}")
    print("request.json:", request.json)
    request_message = request.json['userRequest']['utterance']
    print("request_message:", request_message)
    jjinchin.add_user_message(request_message)
    response = jjinchin.send_request()
    jjinchin.add_response(response)
    response_message = jjinchin.get_response_content()
    jjinchin.handle_token_limit(response)
    jjinchin.clean_context()
    print("response_message:", response_message)
    return format_response(response_message)


if __name__ == "__main__":
    application.run(host='0.0.0.0', port=int(sys.argv[1]))
