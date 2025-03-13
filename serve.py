# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify
import tempfile
import os
from analysis import analyze_excel

app = Flask(__name__)

@app.route('/analyze', methods=['POST'])
def upload_file():
    if 'file' not in request.files or 'question' not in request.form:
        return jsonify({"error": "缺少必要参数"}), 400

    file = request.files['file']
    question = request.form['question']

    if file.filename == '':
        return jsonify({"error": "未选择文件"}), 400
    file_content = file.read()
    file.seek(0)  # 重置文件指针

    file_ext = os.path.splitext(file.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
        filepath = temp_file.name
        file.save(filepath)
    try:
        result = analyze_excel(filepath, question)
    except Exception as e:
        return jsonify({"error": "分析文件失败"}), 500
    finally:
        os.remove(filepath)
    return jsonify({"result": result})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8081)