from flask import Flask, request, jsonify
from openai import OpenAI
from flask_cors import CORS
import os
import tempfile
import logging
import json
import matplotlib.pyplot as plt


# 初始化 Flask
app = Flask(__name__)
CORS(app)  # 允许跨域请求，支持前端调用
plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体字体
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

# 初始化 OpenAI 客户端
client = OpenAI(
    api_key="sk-96d9ffb462c045b0a8f7c4f51268ea23",  # 请替换为你的 API Key
    base_url="https://api.deepseek.com"
)

# 对话历史
messages = [{"role": "system", "content": "You are a helpful assistant."}]

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
            return handle_file_analysis(file, question)
        else:
            print(1)
            return handle_chat(question)

    except Exception as e:
        logging.error(f"请求处理失败: {str(e)}")
        return jsonify({"error": "请求处理失败", "details": str(e)}), 500


def handle_file_analysis(file, question):
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
        # 确保返回的是字典
        if not isinstance(result, dict):
            return jsonify({"error": "分析结果格式不正确"}), 500
        # 如果结果包含图片，转换为可访问的 URL
        if "image" in result:
            result["image"] = f"http://localhost:8081/temp/{os.path.basename(result['image'])}"
        messages.append({"role": "assistant", "content": f"{result}"})
        #result=runse(question,result)
        #print (result)
        #return result
        print(type(result['result']['result']))
        return result['result']
        #return jsonify(result['result'])
    except Exception as e:
        logging.error(f"文件分析失败: {str(e)}")
        return jsonify({"error": "文件分析失败", "details": str(e)}), 500

    finally:
        # 删除临时文件
        if os.path.exists(file_path):
            os.remove(file_path)


def handle_chat(question, error_message=None):
    """处理普通对话"""
    global messages
    try:
        # 记录用户输入
        #然后文本内容可以用markdown形式，该怎么润色你自行判断，比如标题、加粗、行距、缩进。然后文本本身用字符串包装。
        messages.append({"role": "user", "content": f"""{question},
        previous_error:{error_message},
        Note: 
        返回 JSON 字符串。
    
        但是文本本身内容不需要用json的形式，即文本=正常回答，
        但是用result包装你的回答。比如{{'result':文本}}
        然后这一段话不要出现在回答里。
        """})

        # 调用 OpenAI API 进行聊天
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            stream=False,
            response_format={"type": "json_object"}
        )

        # 获取 AI 响应
        assistant_response = response.choices[0].message.content.strip()
        # 确保返回的是字典格式
        if not assistant_response.startswith("{") or not assistant_response.endswith("}"):
            assistant_response = f"{{'result': {assistant_response}}}"
        # 记录 AI 回复
        assistant_response=json.loads(assistant_response)
        messages.append({"role": "assistant", "content": assistant_response['result']})
        print(assistant_response)
        print(type(assistant_response))
        print(assistant_response['result'])
        print(type(assistant_response['result']))
        return assistant_response
    except Exception as e:
        logging.error(f"聊天失败: {str(e)}")
        return jsonify({"error": "聊天失败", "details": str(e)}), 500

def runse(question,result,error_message=None):
    try:
        # 记录用户输入
        messages.append({"role": "user", "content": f"""{question},
        previous_error:{error_message},
        Note: 
        user提问了一个问题{question}，然后{result}是问题结果。
        我希望你能根据结果润色一下回答。
        返回 JSON 字符串。
        然后文本内容可以用markdown形式，该怎么润色你自行判断，比如标题、加粗、行距、缩进。然后文本本身用字符串包装。
        但是文本本身内容不需要用json的形式，即文本=正常回答，
        但是用result包装你的回答。比如{{'result':文本}}
        """})

        # 调用 OpenAI API 进行聊天
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            stream=False,
            response_format={"type": "json_object"}
        )

        # 获取 AI 响应
        assistant_response = response.choices[0].message.content.strip()
        # 确保返回的是字典格式
        if not assistant_response.startswith("{") or not assistant_response.endswith("}"):
            assistant_response = f"{{'result': {assistant_response}}}"
        # 记录 AI 回复
        assistant_response=json.loads(assistant_response)
        messages.append({"role": "assistant", "content": assistant_response['result']})
        print(assistant_response)
        print(type(assistant_response))
        print(assistant_response['result'])
        print(type(assistant_response['result']))
        return assistant_response
    except Exception as e:
        logging.error(f"聊天失败: {str(e)}")
        return jsonify({"error": "聊天失败", "details": str(e)}), 500


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8081)
