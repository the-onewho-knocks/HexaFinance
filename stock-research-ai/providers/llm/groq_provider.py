from groq import AsyncGroq
from loguru import logger

from core.config import settings
from core.exceptions import LLMError
from schemas.llm import LLMRequest, LLMResponse


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
            usage = resp.usage

            return LLMResponse(
                text=choice.message.content or "",
                model=model,
                input_tokens=usage.prompt_tokens if usage else 0,
                output_tokens=usage.completion_tokens if usage else 0,
            )
        except Exception as e:
            logger.error(f"Groq error: {e}")
            raise LLMError(str(e)) from e