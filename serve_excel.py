# -*- coding: utf-8 -*-
import pandas as pd
from openai import OpenAI
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import seaborn as sns
from flask import Flask, request, jsonify, send_from_directory
import json
import os
import tempfile
import logging
from flask_cors import CORS
import serve


app = Flask(__name__)
CORS(app)  # 启用 CORS
logging.basicConfig(level=logging.DEBUG)
conversation_history = []  # 用于存储每个用户的对话历史
tempdir="public\temp"

# 初始化 DeepSeek 客户端
client = OpenAI(api_key="sk-96d9ffb462c045b0a8f7c4f51268ea23", base_url="https://api.deepseek.com")

# 设置支持中文的字体
plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体字体
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题



def load_table_data(file_path):
    try:
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return None

        # 检查文件大小
        #file_size = os.path.getsize(file_path)

        # 手动检查文件扩展名
        if file_path.lower().endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_path)
        elif file_path.lower().endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.lower().endswith('.json'):
            df = pd.read_json(file_path)
        elif file_path.lower().endswith('.parquet'):
            df = pd.read_parquet(file_path)
        else:
            raise ValueError("不支持的文件格式，请提供 Excel (.xlsx, .xls)、CSV (.csv)、JSON (.json) 或 Parquet (.parquet) 文件。")
        return df
    except Exception as e:
        return f"加载表格文件失败: {str(e)}"


def generate_analysis_code(df, question, file_path,error_message=None ):
    context = f"Table structure:\nColumns: {list(df.columns)}\n\nSample data:\n{df.head().to_string(index=False)}"
    if error_message:
        context += f"\n\nPrevious Error:\n{error_message}"

    # 添加当前问题
    serve.messages.append({
        "role": "user",
        "content": f"""
    Context:
    {context}

    Question:
    {question}

    Note: 
    - Generate a complete Python code snippet that can be copied and executed in a blank Python file. 
    - Please respond in json format. 
    - The code should load the data from the file path '{file_path}' and answer the question. 
    - Use the DataFrame 'df' for analysis, do not create new data. 
    - The code must return the result as a dictionary with a 'result' key. 
    - 如果输出没有图片，最后一行代码用这种形式result={{result:XXX}}大括号这种形式.XXX就是问题答案的变量,并且，最后的结果变量名用result保存.
    - Only return the code, no explanations, comments, or Markdown formatting. 
    - If the question involves a specific time range (e.g., 2023-2024), filter the data accordingly. 
    - 如果满足问题条件的有很多人，则一起输出.
    - 自动检测代码，如果代码里有输出： 比如图表的名称，则设置支持中文的字体，但如果没有，则不需要设置。
    - 如果生成了图片。图片路径保存在'C:\\Users\\CZJ\\Desktop\\shanghai\\example\\my-vue-app\\public\\temp'下,并且记录文件名。
    - result={{result:XXX}}，XXX就是文件名。
    
    """
    })

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=serve.messages,
        response_format={"type": "json_object"},
        stream=False
    )

    analysis_code = response.choices[0].message.content.strip()
    print("Generated Code:", analysis_code)  # 打印生成的代码
    return analysis_code

def execute_generated_code(code, df):
    namespace = {'pd': pd, 'df': df, 'plt': plt, 'sns': sns}
    try:
        logging.info("执行生成的代码:")
        logging.info(code)
        exec(code, namespace)

        if 'result' in namespace:
            if 'image' in namespace:
                return True,{'image':namespace['image']}
            else:
                return True, {'result': namespace['result']}
        else:
            return True, {"message": "代码执行成功，但未返回结果"}
    except Exception as e:
        logging.error(f"代码执行失败: {e}")
        return False, f"代码执行失败: {e}"

def analyze_excel(file_path, question):
    df = load_table_data(file_path)

    if df is None:
        return "无法加载表格数据，请检查文件路径。"

    retry_count = 0
    max_retries = 3
    error_message = None

    while retry_count < max_retries:
        analysis_code= generate_analysis_code(df, question, file_path, serve.messages )
        print("\nDeepSeek 生成的分析代码如下：")
        print(analysis_code)
        try:
            generated_code_dict = json.loads(analysis_code)
            generated_code = generated_code_dict.get('code')

            if generated_code:
                print("\n生成的 Python 代码：")
                print(generated_code)
                success, result = execute_generated_code(generated_code, df)
                if success:
                    print("\n代码执行结果：")
                    print(result)
                    return result
                else:
                    error_message = result
                    retry_count += 1
                    print(f"尝试次数: {retry_count}/{max_retries}")
            else:
                return "未找到有效的 Python 代码。"
        except json.JSONDecodeError as e:
            return f"解析 JSON 数据失败: {e}"
    else:
        return "达到最大重试次数，无法生成有效代码。"


"""
@app.route('/temp/<path:filename>')
def serve_temp_file(filename):
    return send_from_directory(filename)

@app.route('/analyze', methods=['POST'])
def upload_file():
    if 'file' not in request.files or 'question' not in request.form:
        return jsonify({"error": "缺少必要参数"}), 400

    file = request.files['file']
    question = request.form['question']

    # 检查文件是否为空
    if file.filename == '':
        return jsonify({"error": "未选择文件"}), 400

    # 保存到临时文件
    file_ext = os.path.splitext(file.filename)[1]  # 获取文件扩展名
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
        file_path = temp_file.name
        file.save(file_path)

    try:
        # 调用分析函数
        result = analyze_excel(file_path, question, conversation_history)

        # 检查结果是否为字典
        if not isinstance(result, dict):
            return jsonify({"error": "分析结果格式不正确"}), 500

        # 如果结果中包含图片路径，转换为 URL
        if 'image' in result:
            result['image'] = f"http://localhost:8081/temp/{os.path.basename(result['image'])}"
        # 返回结果
        return jsonify({"result": result})
    except Exception as e:
        # 记录错误日志
        logging.error(f"分析文件失败: {str(e)}")
        return jsonify({"error": "分析文件失败", "details": str(e)}), 500
    finally:
        # 删除临时文件
        if os.path.exists(file_path):
            os.remove(file_path)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8081)
"""