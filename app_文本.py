# -*- coding: utf-8 -*-
import pandas as pd
from openai import OpenAI
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import seaborn as sns
from flask import Flask, request, jsonify
import json
import os
import tempfile
import logging
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # 启用 CORS
logging.basicConfig(level=logging.DEBUG)


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
        file_size = os.path.getsize(file_path)

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


def generate_analysis_code(df, question, file_path, error_message=None):
    context = f"Table structure:\nColumns: {list(df.columns)}\n\nSample data:\n{df.head().to_string(index=False)}"
    if error_message:
        context += f"\n\nPrevious Error:\n{error_message}"
    TEMP_DIR = tempfile.gettempdir()  # 临时图片存放目录
    messages = [
        {"role": "system",
         "content": "You are a helpful assistant that generates Python code to analyze tabular data."},
        {"role": "user",
         "content": f"Context:\n{context}\n\nQuestion:\n{question}\n\nNote: Generate a complete Python code snippet that can be copied and executed in a blank Python file. Please respond in json format. The code should load the data from the file path '{file_path}' and answer the question.如果返回的代码会生成图片，那么输出的图片保存在{TEMP_DIR}。Use the DataFrame 'df' for analysis, do not create new data. The code must return the result as a dictionary with a 'result' key. Only return the code, no explanations, comments, or Markdown formatting. If the question involves a specific time range (e.g., 2023-2024), filter the data accordingly.自动检测代码，如果代码里有输出： 比如图表的名称，则设置支持中文的字体，但如果没有，则不需要设置。在生成图表后，显式关闭 Matplotlib 的资源。例如加入这段代码plt.close('all')  # 关闭所有 Matplotlib 资源"},
        {"role": "assistant", "content": ""}
    ]

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        response_format={"type": "json_object"},
        stream=False
    )

    analysis_code = response.choices[0].message.content.strip()
    return analysis_code


def execute_generated_code(code, df):
    namespace = {'pd': pd, 'df': df, 'plt': plt, 'sns': sns}
    try:
        # 执行生成的代码
        exec(code, namespace)
        # 检查是否有返回结果
        if 'result' in namespace:
            return True, namespace['result']
        else:
            return True, {"message": "代码执行成功，但未返回结果"}
    except Exception as e:

        return False, f"代码执行失败: {e}"

def analyze_excel(file_path, question):
    """
    分析Excel或CSV表格数据。
    :param file_path: 文件路径
    :param question: 用户的问题
    :return: 分析结果或错误信息
    """
    df = load_table_data(file_path)

    if df is None:
        return "无法加载表格数据，请检查文件路径。"

    retry_count = 0
    max_retries = 3
    error_message = None

    while retry_count < max_retries:
        analysis_code = generate_analysis_code(df, question, file_path, error_message)

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


@app.route('/analyze', methods=['POST'])
def upload_file():
    if 'file' not in request.files or 'question' not in request.form:
        return jsonify({"error": "缺少必要参数"}), 400

    file = request.files['file']
    question = request.form['question']

    # 检查文件是否为空
    if file.filename == '':
        return jsonify({"error": "未选择文件"}), 400

    # 打印文件名和内容
    file_content = file.read()
    file.seek(0)  # 重置文件指针

    # 保存到临时文件，并确保文件扩展名正确
    file_ext = os.path.splitext(file.filename)[1]  # 获取文件扩展名
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
        filepath = temp_file.name
        file.save(filepath)

    try:
        result = analyze_excel(filepath, question)
    except Exception as e:
        return jsonify({"error": "分析文件失败"}), 500
    finally:
        # 删除临时文件
        os.remove(filepath)
    return jsonify({"result": result})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8081)

