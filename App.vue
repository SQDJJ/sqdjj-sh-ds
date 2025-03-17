<template>
    <div class="app">
        <h1>文件与问题提交</h1>

        <!-- 文件选择 -->
        <div class="form-group">
            <label for="fileInput">选择文件:</label>
            <input type="file" id="fileInput" @change="onFileChange" />
        </div>

        <!-- 问题输入 -->
        <div class="form-group">
            <label for="questionInput">输入问题:</label>
            <input v-model="question" type="text" id="questionInput" placeholder="请输入您的问题" />
        </div>

        <!-- 提交按钮 -->
        <button @click="submitFileAndQuestion" :disabled="!file || !question">提交</button>

        <!-- 显示结果 -->
        <div v-if="result" class="result">
            <h2>分析结果:</h2>
            <pre>{{ result }}</pre>
        </div>

        <!-- 错误信息 -->
        <div v-if="error" class="error">
            <p>{{ error }}</p>
        </div>
    </div>
</template>

<script setup>
    import { ref } from 'vue'
    import axios from 'axios'

    // 响应式数据
    const file = ref(null)
    const question = ref('')
    const result = ref('')
    const error = ref('')

    // 处理文件选择变化
    function onFileChange(event) {
        file.value = event.target.files[0]
    }

    // 提交文件和问题
    async function submitFileAndQuestion() {
        if (!file.value || !question.value) {
            error.value = '请先选择文件并输入问题！'
            return
        }

        const formData = new FormData()
        formData.append('file', file.value)
        formData.append('question', question.value)

        try {
            const response = await axios.post('http://localhost:8081/analyze', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data'
                }
            })
            console.log('后端返回的数据:', response.data) // 打印后端返回的数据
            result.value = response.data.result
            console.log('后端返回的数据:', result.value)
            error.value = ''
        } catch (err) {
            console.error('Error submitting file and question:', err)
            error.value = '提交文件和问题时发生错误，请稍后再试。'
            result.value = ''
        }
    }
</script>

<style scoped>
    .app {
        max-width: 600px;
        margin: 0 auto;
        padding: 20px;
        border: 1px solid #ccc;
        border-radius: 5px;
        background-color: #f9f9f9;
    }

    .form-group {
        margin-bottom: 15px;
    }

    label {
        display: block;
        margin-bottom: 5px;
    }

    input[type="file"], input[type="text"] {
        width: 100%;
        padding: 8px;
        margin-bottom: 10px;
        border: 1px solid #ccc;
        border-radius: 4px;
    }

    button {
        padding: 10px 20px;
        background-color: #4CAF50;
        color: white;
        border: none;
        border-radius: 4px;
        cursor: pointer;
    }

        button:disabled {
            background-color: #ccc;
            cursor: not-allowed;
        }

    .result, .error {
        margin-top: 20px;
        padding: 10px;
        border-radius: 4px;
    }

    .result {
        background-color: #e6ffe6;
        color: green;
    }

    .error {
        background-color: #ffe6e6;
        color: red;
    }
</style>