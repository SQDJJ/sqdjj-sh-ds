from flask import Flask, request, jsonify
from openai import OpenAI
from flask_cors import CORS
import os
import tempfile
import logging
import json
import matplotlib.pyplot as plt
import matplotlib
import time
import threading
from llm_client import LLMClient
matplotlib.use('Agg')  # 使用非交互式后端
# 初始化 Flask
app = Flask(__name__)
CORS(app)  # 允许跨域请求，支持前端调用
plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体字体
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
start_time=time.time()
os.environ["http_proxy"] = "http://10.177.44.113:7890"
os.environ["https_proxy"] = "http://10.177.44.113:7890"
# 初始化 OpenAI 客户端
# 读取配置文件
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)
# 初始化 LLMClient
llm = LLMClient(
    api_key=config["api_key"],      # 必须存在，否则报错
    base_url=config.get("base_url"), # 如果键不存在返回 None
    model=config["model"]
)
# 对话历史
messages = [{"role": "system", "content": "You are a helpful assistant."}]
messages_lock = threading.Lock()

@app.route("/chat", methods=["POST"])
def chat_or_analyze():
    """处理聊天或文件分析请求"""
    try:
        # 获取用户输入的问题
        question = request.form.get("question", "").strip()
        # 检查输入是否为空
        if not question:
            return jsonify({"error": "输入不能为空"}), 400
        # 检查是否上传了文件
        file = request.files.get("file")
        if file:
            print(0)
            result = handle_file_analysis(file, question)
            return result
        else:
            print(1)
            return handle_chat(question)

    except Exception as e:
        logging.error(f"请求处理失败: {str(e)}", exc_info=True)  # 记录完整的异常堆栈
        return jsonify({"error": "请求处理失败", "details": str(e)}), 500


def handle_file_analysis(file, question):
    start_time = time.time()
    from serve_excel import analyze_excel
    """处理 Excel 文件分析"""
    global messages
    try:
        # 检查文件是否为空
        if file.filename == '':
            return jsonify({"error": "未选择文件"}), 400
        # 保存文件到临时目录
        file_ext = os.path.splitext(file.filename)[1]  # 获取文件扩展名
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            file_path = temp_file.name
            file.save(file_path)
        # 调用 `analyze_excel` 进行分析
        result = analyze_excel(file_path, question)
        print(123)
        # 确保返回的是字典
        if not isinstance(result, dict):
            return jsonify({"error": "分析结果格式不正确"}), 500
        print(1)
        # 如果结果包含图片，转换为可访问的 URL
        if "image" in result:
            result["image"] = f"http://localhost:8081/temp/{os.path.basename(result['image'])}"
        print(2)
        #messages.append({"role": "assistant", "content": f"{result}"})
        print(3)
        try:
            # 尝试执行 if 条件判断
            if str(result['result']['result']).endswith('.png') or str(result['result']).endswith('.png'):
                end_time = time.time()
                ti = end_time - start_time
                print(ti)
                return result['result']
            else:
                print(234)
                result = runse(question, result)
                return result
        except Exception as e:  # 捕获 if 条件中可能发生的任何异常
            print(f"条件判断出错，执行 else 语句。错误: {e}")
            print(234)
            result = runse(question, result)
            return result
    except Exception as e:
        logging.error(f"文件分析失败: {str(e)}")
        return jsonify({"error": "文件分析失败", "details": str(e)}), 500
    finally:
        # 删除临时文件
        if os.path.exists(file_path):
            os.remove(file_path)


def handle_chat(question, error_message=None):
    """处理普通对话"""
    start_time=time.time()
    global messages
    try:
        # 记录用户输入
        messages.append({"role": "user", "content": f"""{question},
        previous_error:{error_message},
        Note: 
        返回 JSON 字符串。
        不要markdown的形式，不需要换行等符号
        但是文本本身内容不需要用json的形式，即文本=正常回答，
        但是用result包装你的回答。比如{{'result':文本}}
        然后这一段话不要出现在回答里。
        """})
        '''
        # 调用 OpenAI API 进行聊天
        response = client.chat.completions.create(
            model='deepseek-chat',
            messages=messages,
            stream=False,
            response_format={"type": "json_object"}
        )

        # 获取 AI 响应
        assistant_response = response.choices[0].message.content.strip()
        '''
        assistant_response = llm.chat(messages)  # 调用封装好的 LLMClient
        # 确保返回的是字典格式
        if not assistant_response.startswith("{") or not assistant_response.endswith("}"):
            assistant_response = f"{{'result': {assistant_response}}}"
        # 记录 AI 回复
        assistant_response = json.loads(assistant_response)
        #append({"role": "assistant", "content": assistant_response['result']})
        end_time=time.time()
        ti=end_time-start_time
        print(ti)
        print(messages)
        print(len(messages))
        return assistant_response
    except Exception as e:
        logging.error(f"聊天失败: {str(e)}")
        return jsonify({"error": "聊天失败", "details": str(e)}), 500

def runse(question, result, error_message=None):
    try:
        # 然后文本内容可以用markdown形式，该怎么润色你自行判断，比如标题、加粗、行距、缩进。然后文本本身用字符串包装。
        #with messages_lock:
            # 记录用户输入
            messages.append({"role": "user", "content": f"""{question},
            previous_error:{error_message},
            Note: 
            user提问了一个问题{question}，然后{result}是问题结果。
            我希望你能根据结果润色一下回答。不需要怎么说明，只是简要回答一下问题就行。
            返回 JSON 字符串。
            不要markdown的形式，不需要换行等符号
            但是文本本身内容不需要用json的形式，即文本=正常回答，
            但是用result包装你的回答。比如{{'result':文本}}
            """})
            '''
            # 调用 OpenAI API 进行聊天
            response = client.chat.completions.create(
                model='deepseek-chat',
                messages=messages,
                stream=False,
                response_format={"type": "json_object"}
            )
            # 获取 AI 响应
            assistant_response = response.choices[0].message.content.strip()
            '''
            assistant_response = llm.chat(messages)  # 调用封装好的 LLMClient
            # 确保返回的是字典格式
            if not assistant_response.startswith("{") or not assistant_response.endswith("}"):
                assistant_response = f"{{'result': {assistant_response}}}"
            # 记录 AI 回复
            assistant_response = json.loads(assistant_response)
            messages.append({"role": "assistant", "content": assistant_response['result']})
            print(messages)
            #print(type(assistant_response))
            #print(assistant_response['result'])
            #print(type(assistant_response['result']))
            return assistant_response
    except Exception as e:
        logging.error(f"聊天失败: {str(e)}")
        return jsonify({"error": "聊天失败", "details": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8081, debug=True)

