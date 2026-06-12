from core.constants import DEFAULT_LLM_PROVIDER
from schemas.llm import LLMRequest, LLMResponse
from providers.llm.gemini_provider import GeminiProvider
from providers.llm.groq_provider import GroqProvider

class LLMGateway:
    """Single entry point; routes to Gemini or Groq."""

    def __init__(self, provider: str = DEFAULT_LLM_PROVIDER):
        self._provider = provider
        self._gemini = GeminiProvider()
        self._groq = GroqProvider()

    async def complete(self, req: LLMRequest) -> LLMResponse:
        if self._provider == "groq":
            return await self._groq.complete(req)
        return await self._gemini.complete(req)

    async def complete_text(self, prompt: str, system: str | None = None) -> str:
        resp = await self.complete(LLMRequest(prompt=prompt, system=system))
        return resp.text