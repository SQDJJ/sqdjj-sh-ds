<template>
    <div class="whole">
      <h1></h1>
      <div class="top-left">左上角</div>
      <div class="top-right">生气对讲机</div>
  
      <div class="app">
          <!-- 显示对话历史 -->
            <div class="chat-history" ref="chatContainer">
                <div v-if="chatHistory.length > 0">
                    <div v-for="(message, index) in chatHistory" :key="index" :class="['message-container', message.role === 'user' ? 'user-container' : 'assistant-container']">
                        <p v-if="message.role === 'user'" class="user-message">{{ message.content }}</p>
                        <p v-else class="assistant-message" v-html="message.content"></p>
                        <div v-if="message.role === 'user'" class="label-circle1">我</div>
                        <div v-if="message.role === 'assistant'" class="label-circle2">答</div>
                    </div>
                </div>
                <div v-else class="nonehistory">
                    <p>暂无对话历史</p>
                </div>
            </div>

  
          <!-- 输入框 -->
            <div class="input-container">
                <!-- 文件上传 -->
                <div class="file-upload">
                    <input type="file" id="fileInput" @change="handleFileUpload" accept=".xlsx" />
                    <p v-if="selectedFile">已选择文件: {{ selectedFile.name }}</p>
                </div>
              <textarea
                v-model="question"
                id="questionInput"
                placeholder="请输入您的问题"
                @input="adjustTextareaHeight"
                :style="{ height: textareaHeight + 'px' }"
              ></textarea>
              <button @click="submitFileAndQuestion" :disabled="isProcessing || (!question && !selectedFile)">提交</button>
            </div>
          </div>
    </div>
</template>
  
<script setup>
import { ref, onMounted, nextTick } from 'vue'
import axios from 'axios'
import { marked } from 'marked'; // 如果使用 npm 安装

// 响应式数据
const question = ref('')
const error = ref('')
const chatHistory = ref([])  // 保存对话历史
const textareaHeight = ref(40)  // 输入框初始高度
const chatContainer = ref(null)  // 绑定 ref
const selectedFile = ref(null)  // 选中的文件
const isProcessing = ref(false)  // 是否正在处理请求

// 处理文件上传
function handleFileUpload(event) {
    const file = event.target.files[0]
    if (file) {
        selectedFile.value = file
    }
}

// 提交问题或文件并获取回答
async function submitFileAndQuestion(event) {
    event.preventDefault(); // 阻止默认提交行为
    if (!question.value && !selectedFile.value) {
        error.value = '请输入问题或上传文件！'
        return
    }
    isProcessing.value = true  // 开始处理时设置为true
    const formData = new FormData()
    if (question.value) {
        formData.append('question', question.value)
        chatHistory.value.push({ role: 'user', content: question.value })
    if (selectedFile.value) {
        formData.append('file', selectedFile.value)
    }
        // 清空输入框和文件
            question.value = ''
            selectedFile.value = null
            document.getElementById('fileInput').value = '' // 清空文件输入框
            textareaHeight.value = 40
            document.getElementById('questionInput').style.height = 'auto'
        // 滚动到底部
            await nextTick()
            scrollToBottom()
    }

    try {
    const response = await axios.post('http://localhost:8081/chat', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    });
    console.log('后端返回的数据:', response.data); // 打印后端返回的数据

    // 解析后端返回的数据
    const assistantReply = response.data.result || response.data.reply || "抱歉，未能生成回答";

    // 判断是否是图片文件
    if (typeof assistantReply === 'string' && assistantReply.endsWith('.png')) {
        // 拼接相对路径
        const relativePath = `/temp/${assistantReply}`;
        // 使用相对路径加载图片
        const imageHtml = `<div style="text-align: center;"><img src="${relativePath}" alt="生成的图片" style="max-width: 100%; height: auto;"></div>`;
        chatHistory.value.push({ role: 'assistant', content: imageHtml });
    } else {
        // 如果不是图片，直接添加文本内容
        const assistantReply1 = JSON.stringify(assistantReply, null, 2); // 格式化 JSON 数据
        chatHistory.value.push({ role: 'assistant', content: assistantReply1 });
    }
} catch (err) {
    // 将具体的错误信息作为 assistant 的回答
    const errorMessage = err.response?.data?.message || err.message || '请求失败，请检查后端是否运行正常！';
    chatHistory.value.push({ role: 'assistant', content: `请求失败：${errorMessage}` });
    error.value = errorMessage; // 将错误信息存储到 error 变量中
} finally {
    isProcessing.value = false; // 请求结束后无论成功失败都设置为 false
    await nextTick();
    scrollToBottom();
}
}

// 输入框自适应高度
function adjustTextareaHeight() {
    const textarea = document.getElementById('questionInput')
    if (textarea) {
        textarea.style.height = 'auto'
        const newHeight = textarea.scrollHeight
        if (newHeight > 200) {
            textarea.style.height = '200px'
            textarea.style.overflowY = 'scroll'
        } else {
            textarea.style.height = newHeight + 'px'
            textarea.style.overflowY = 'hidden'
        }
    }
}

// 滚动到底部
function scrollToBottom() {
    if (chatContainer.value) {
        chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
}

// 组件加载后，滚动到底部
onMounted(() => {
    scrollToBottom()
})
</script>
  

<style scoped>
/* 整体布局 */
html, body {
    height: 100%; /* 确保 html 和 body 高度为 100% */
    width: 100%;
    margin: 0; /* 去除默认的 margin */
    padding: 0; /* 去除默认的 padding */
}
.whole {
    display: flex;
    flex-direction: column;
    align-items: center;
    /*justify-content: center;*/
    height: 97.5vh;       /*设置元素的高度为其父容器（通常是视窗）高度的97% */
    width: 100%;
    background-color: #ffffff;  /*背景 */
    font-family: Arial, sans-serif; /*文本 */
    overflow: hidden;
}


/* 左上角 */
.top-left {
    position: absolute;
    top: 10px;
    left: 10px;
    font-size: 1.2rem;
    color: #555;
}

/* 右上角 */
.top-right {
    position: absolute;
    top: 10px;
    right: 10px;
    font-size: 1.2rem;
    color: #555;
}

/* 聊天应用容器 */
.app {
    background-color: #fff;
    display: flex;
    flex-direction: column;
    gap: 20px;
    width:80%;
    box-sizing: border-box;
    height: 100vh;
    border: 2px solid#ffffff;
    justify-content: space-between;
    overflow: hidden;
}

/* 聊天历史记录 */
.chat-history {
    flex-grow: 1;
    overflow-y: auto;
    padding: 10px;
    border-radius: 5px;
    background-color: #f9f9f9;
    max-height: 600px;
    border: 2px solid#ffffff;
    width:100%;
    box-sizing: border-box;
    background-image: url('/public/temp/2.jpg'); /* 图片路径 */
    background-size: cover; /* 背景图覆盖整个容器 */
    background-position: center; /* 背景图居中 */
    background-repeat: no-repeat; /* 背景图不重复 */
    z-index: 1;
}

/* 消息容器 */
.message-container {
    display: flex;
    align-items: flex-start; /* 顶部对齐 */
    margin-bottom: 10px; /* 消息之间的间距 */
}

/* 用户消息容器（靠右） */
.user-container {
    justify-content: flex-end; /* 靠右对齐 */
    z-index: 0;
}

/* 助手消息容器（靠左） */
.assistant-container {
    justify-content: flex-start; /* 靠左对齐 */
    z-index: 0;
}

/* 用户消息样式 */
.user-message {
    background-color: #e3f2fd; /* 用户消息背景色 */
    padding: 10px;
    border-radius: 10px;
    max-width: 70%; /* 限制消息宽度 */
    margin-left: auto; /* 靠右对齐 */
    order: 1; /* 消息在左侧 */
    white-space: pre-wrap; /* 保持空白符和换行符 */
    z-index: 2;
}

/* 助手消息样式 */
.assistant-message {
    background-color: #f5f5f5; /* 助手消息背景色 */
    padding: 10px;
    border-radius: 10px;
    max-width: 70%; /* 限制消息宽度 */
    margin-right: auto; /* 靠左对齐 */
    order: 1; /* 消息在左侧 */
    white-space: pre-wrap; /* 保持空白符和换行符 */
    z-index: 2;
}

.assistant-message img {
    max-width: 100%;
    height: auto;
    border-radius: 10px;
    margin: 10px 0;
}

/* 标签圆圈 */
.label-circle1 {
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background-color: #007bff;
    color: #fff;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.8rem;
    margin-top: 5px;
    margin-left: 10px; /* 用户消息标签的左边距 */
    margin-right: 10px; /* 助手消息标签的右边距 */
    order: 2; /* 标签在右侧 */
}



.label-circle2{
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background-color: #007bff;
    color: #fff;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.8rem;
    margin-top: 5px;
    margin-left: 10px; /* 用户消息标签的左边距 */
    margin-right: 10px; /* 助手消息标签的右边距 */
    order: -2; /* 标签在右侧 */
}

/* 输入框容器 */
.input-container {
    display: flex;
    flex-direction: column;
    gap: 10px;
    bottom:30px;
}

/* 文件上传 */
.file-upload {
    display: flex;
    align-items: center;
    gap: 10px;
}

/* 文本输入框 */
textarea {
    width: 95%;
    padding: 10px;
    border: 1px solid #150ae3;
    border-radius: 5px;
    resize: none;
    font-size: 1rem;
    line-height: 1.5;
}

/* 提交按钮 */
button {
    padding: 10px 20px;
    background-color: #007bff;
    color: #fff;
    border: none;
    border-radius: 5px;
    cursor: pointer;
    font-size: 1rem;
}

button:disabled {
    background-color: #ccc;
    cursor: not-allowed;
}

.nonehistory {
    display: flex;
    justify-content: center; /* 水平居中 */
    align-items: center; /* 垂直居中 */
    color: #999; /* 设置文本颜色 */
    font-size: 1.2rem; /* 设置字体大小 */
}

</style>