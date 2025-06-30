# claude_api.py
import os, anthropic

class ClaudeAPI:
    """
    Mimic GeminiAPI / OpenAIAPI interface:
        llm(messages=[{"role":"user","content":"hi"}], temperature=0.7)
    and expose `self.response` for downstream code.
    """
    def __init__(self, api_key: str or None = None,
                 model_name: str = "claude-3-sonnet-20240229"):
        api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise EnvironmentError("請先設定 ANTHROPIC_API_KEY")
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model_name = model_name
        self.response = None
        # token usage (optional)
        self.prompt_tokens = self.completion_tokens = self.total_tokens = 0

    def __call__(self, messages, temperature=0.7, max_tokens=2048, **kw):
        """
        Accept OpenAI-style messages list, convert to Anthropic format, return
        dict with 'choices'[0]['message']['content'] so Structurizer / Utilizer
        can keep the same code.
        """
        # Claude 要求每段 content 為 str；role 支援 system / user / assistant
        resp = self.client.messages.create(
            model=self.model_name,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=messages,
            **kw
        )
        self.response = resp
        choice = resp.content[0].text if resp.content else ""

        # usage 計算
        usage = resp.usage
        self.prompt_tokens     = usage.input_tokens
        self.completion_tokens = usage.output_tokens
        self.total_tokens      = usage.input_tokens + usage.output_tokens

        return {
            "choices": [{
                "message": {"role": "assistant", "content": choice},
                "finish_reason": resp.stop_reason,
            }],
            "model": self.model_name,
        }
