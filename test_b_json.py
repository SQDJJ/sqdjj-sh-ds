# -*- coding: utf-8 -*-
import pandas as pd
from openai import OpenAI
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import seaborn as sns
import json
import os
import time

# 初始化 DeepSeek 客户端
client = OpenAI(api_key="sk-96d9ffb462c045b0a8f7c4f51268ea23", base_url="https://api.deepseek.com")

# 设置支持中文的字体
plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体字体
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题


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


def load_table_data(file_path):
    try:
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return None

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

    messages = [
        {"role": "system",
         "content": "You are a helpful assistant that generates Python code to analyze tabular data."},
        {"role": "user",
         "content": f"Context:\n{context}\n\nQuestion:\n{question}\n\nNote: Generate a complete Python code snippet that can be copied and executed in a blank Python file. Please respond in json format. The code should load the data from the file path '{file_path}' and answer the question. Use the DataFrame 'df' for analysis, do not create new data. The code must return the result as a dictionary with a 'result' key. Only return the code, no explanations, comments, or Markdown formatting. If the question involves a specific time range (e.g., 2023-2024), filter the data accordingly.自动检测代码，如果代码里有输出： 比如图表的名称，则设置支持中文的字体，但如果没有，则不需要设置。在生成图表后，显式关闭 Matplotlib 的资源。例如加入这段代码plt.close('all')  # 关闭所有 Matplotlib 资源"},
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
            return True, {"message": "代码执行成功", "result": namespace['result']}
        else:
            return True, {"message": "代码执行成功，但未返回结果"}
    except Exception as e:
        return False, f"代码执行失败: {e}"



if __name__ == '__main__':
    start_time = time.time()

    # 示例输入
    file_path = r"C:\Users\CZJ\Desktop\课程论文\all_data.xlsx"  # 替换为你的文件路径
    question = "这是1990-2023年的中国人口和一些母婴用品行业（母婴，奶粉，牙膏，纸尿布）相关数据，但是母婴行业有年份数据欠缺。以人口数据为自变量，母婴行业相关数据为因变量，分别计算他们的皮尔森相关系数。"  # 替换为你的问题

    # 确保文件存在
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")


    # 执行分析
    result = analyze_excel(file_path, question)
    print("分析结果:", result)

    end_time = time.time()
    total_time = end_time - start_time
    print(f"总耗时: {total_time:.2f} 秒")