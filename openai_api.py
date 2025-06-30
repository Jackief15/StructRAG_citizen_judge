# openai_api.py
import os, functools, openai

class OpenAIAPI:
    def __init__(self, api_key=None, model_name="gpt-4o-mini"):
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError("OPENAI_API_KEY 未設定")
        # 1.x 寫法：建立 client 物件
        self.client = openai.OpenAI(api_key=api_key)
        self.model_name = model_name
        self.response = None

    def __call__(self, messages, temperature=0.7, max_tokens=2048, **kw):
        resp = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kw
        )
        self.response = resp      # 保留完整物件
        choice = resp.choices[0].message.content

        # usage 統計
        usage = resp.usage
        self.prompt_tokens     = usage.prompt_tokens
        self.completion_tokens = usage.completion_tokens
        self.total_tokens      = usage.total_tokens

        return {
            "choices": [{
                "message": {"role": "assistant", "content": choice},
                "finish_reason": resp.choices[0].finish_reason
            }],
            "model": self.model_name
        }
