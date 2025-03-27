from openai import OpenAI
import json

class LLMClient:
    def __init__(self, api_key, base_url=None, model="deepseek-chat"):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def chat(self, messages):
        """调用 LLM 进行聊天"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=False,
            response_format={"type": "json_object"}
        )
        # 获取并打印 token 消耗的信息
        usage = response.usage
        print(f"Prompt tokens: {usage.prompt_tokens}")
        print(f"Completion tokens: {usage.completion_tokens}")
        return response.choices[0].message.content

    def set_model(self, model):
        """动态更改大模型"""
        self.model = model
