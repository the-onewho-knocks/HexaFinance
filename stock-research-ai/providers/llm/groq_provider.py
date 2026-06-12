from groq import AsyncGroq
from core.config import settings
from core.exceptions import LLMError
from schemas.llm import LLMRequest, LLMResponse
from loguru import logger

class GroqProvider:
    def __init__(self):
        self._client = AsyncGroq(api_key=settings.groq_api_key)

    async def complete(self, req: LLMRequest) -> LLMResponse:
        model = req.model or "llama-3.3-70b-versatile"
        messages = []
        if req.system:
            messages.append({"role": "system", "content": req.system})
        messages.append({"role": "user", "content": req.prompt})

        try:
            resp = await self._client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=req.max_tokens,
                temperature=req.temperature,
            )
            choice = resp.choices[0]
            return LLMResponse(
                text=choice.message.content or "",
                model=model,
                input_tokens=resp.usage.prompt_tokens,
                output_tokens=resp.usage.completion_tokens,
            )
        except Exception as e:
            logger.error(f"Groq error: {e}")
            raise LLMError(str(e)) from e