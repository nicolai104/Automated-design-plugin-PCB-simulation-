from typing import Optional, Dict, Any
import os
import json

try:
    import openai
except ImportError:
    openai = None


class OpenAIClient:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.model = os.getenv("LLM_MODEL", "glm-4")
        self.base_url = os.getenv("OPENAI_BASE_URL", "").rstrip("/")

        if self.api_key and openai:
            openai.api_key = self.api_key
            if self.base_url:
                openai.api_base = self.base_url
        else:
            print("Warning: OpenAI API key not set, using mock responses")

    async def generate(self, prompt: str, **kwargs) -> str:
        if not self.api_key or not openai:
            return self._mock_generate(prompt)

        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an AI assistant specialized in PCB design and circuit simulation."},
                    {"role": "user", "content": prompt}
                ],
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 2000)
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"API error: {e}")
            return self._mock_generate(prompt)

    def _mock_generate(self, prompt: str) -> str:
        if "layout" in prompt.lower():
            return json.dumps({
                "components": [],
                "warnings": ["使用模拟响应"]
            })
        elif "simulation" in prompt.lower():
            return json.dumps({
                "type": "Transient",
                "data": [0.0] * 100,
                "success": True,
                "message": "仿真完成（模拟）"
            })
        else:
            return "我是AI PCB设计助手。我可以帮助您进行PCB布局、电路仿真和设计分析。请告诉我您的需求。"


class ClaudeClient:
    def __init__(self):
        self.api_key = os.getenv("CLAUDE_API_KEY", "")
        self.model = os.getenv("CLAUDE_MODEL", "claude-3-opus-20240229")

    async def generate(self, prompt: str, **kwargs) -> str:
        if not self.api_key:
            return "Claude API key not configured"

        return "Claude integration coming soon"


def get_llm_client(provider: str = "openai") -> Any:
    if provider == "openai":
        return OpenAIClient()
    elif provider == "claude":
        return ClaudeClient()
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")
