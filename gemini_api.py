# gemini_api.py
import os, time, functools
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from typing import List, Dict, Any

# 同時接受兩種環境變數名稱
api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
if not api_key:
    raise EnvironmentError("請設定 GOOGLE_API_KEY / GEMINI_API_KEY")
genai.configure(api_key=api_key)

@functools.lru_cache()
def _get_model(name: str):
    return genai.GenerativeModel(name)

class GeminiAPI:
    def __init__(self, model_name="gemini-2.0-flash"):
        self.model_name = model_name
        self.model = _get_model(model_name)
        self.response = None
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.total_tokens = 0

    # def __call__(
    #     self,
    #     messages: List[Dict[str, str]],
    #     temperature: float = 0.7,
    #     max_tokens: int = 2048,
    #     retry: int = 3,
    #     **kwargs,
    # ) -> Dict[str, Any]:
    #     prompt = self._msgs_to_prompt(messages)
    #     gen_cfg = dict(temperature=temperature, max_output_tokens=max_tokens, **kwargs)

    #     for attempt in range(retry):
    #         try:
    #             resp = self.model.generate_content(prompt, generation_config=gen_cfg)
    #             return {
    #                 "choices": [{
    #                     "message": {"role": "assistant", "content": resp.text},
    #                     "finish_reason": "stop",
    #                 }],
    #                 "model": self.model_name,
    #                 "usage": {
    #                     "prompt_tokens": 0,
    #                     "completion_tokens": getattr(resp, "token_count", 0),
    #                     "total_tokens": 0,
    #                 },
    #             }
    #         except Exception as e:
    #             if attempt == retry - 1:
    #                 raise
    #             time.sleep(1)
    #     wrapped = {
    #         "choices": [{
    #             "message": {"role": "assistant", "content": resp.text},
    #             "finish_reason": "stop",
    #         }],
    #         "model": self.model_name,
    #     }
    #     self.response = wrapped        # ← 關鍵補這行
    #     self.completion_tokens = getattr(resp, "token_count", 0)
    #     self.total_tokens = self.prompt_tokens + self.completion_tokens
    #     return wrapped

    def __call__(self, messages, temperature=0.7, max_tokens=2048, retry=3, **kwargs):
        prompt = self._msgs_to_prompt(messages)
        gen_cfg = dict(temperature=temperature, max_output_tokens=max_tokens, **kwargs)

        for attempt in range(retry):
            try:
                resp = self.model.generate_content(
                    prompt, 
                    generation_config=gen_cfg,
                    safety_settings={
                        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                    }
                )

                # === 1. 把 Gemini 回傳包成 OpenAI 兼容格式
                wrapped = {
                    "choices": [{
                        "message": {
                            "role": "assistant",
                            "content": resp.text,
                        },
                        "finish_reason": "stop",
                    }],
                    "model": self.model_name,
                }

                # === 2. 關鍵：更新實例屬性
                self.response = wrapped                    # ←★★★
                self.completion_tokens = getattr(resp, "token_count", 0)
                self.prompt_tokens = 0
                self.total_tokens = self.prompt_tokens + self.completion_tokens

                # === 3. 回傳
                return wrapped

            except Exception as e:
                if attempt == retry - 1:
                    raise
                time.sleep(1)


    @staticmethod
    def _msgs_to_prompt(msgs: List[Dict[str, str]]) -> str:
        parts = []
        for m in msgs:
            role, content = m.get("role"), m.get("content", "")
            tag = {"system": "[System]", "user": "[User]", "assistant": "[Assistant]"}\
                  .get(role, role)
            parts.append(f"{tag}\n{content}")
        return "\n\n".join(parts)
