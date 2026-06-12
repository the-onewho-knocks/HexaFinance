from google import genai
from google.genai import types
from core.config import settings
from core.exceptions import LLMError
from schemas.llm import LLMRequest, LLMResponse
from loguru import logger

class GeminiProvider:
    def __init__(self):
        self._client = genai.Client(
            api_key=settings.gemini_api_key
            )

    async def complete(self, req: LLMRequest) -> LLMResponse:
        model = req.model or "gemini-2.0-flash"
        contents = []
        if req.system:
            contents.append(types.Content(role="user", parts=[types.Part(text=req.system)]))
            contents.append(types.Content(role="model", parts=[types.Part(text="Understood.")]))
        contents.append(types.Content(role="user", parts=[types.Part(text=req.prompt)]))

        try:
            response = self._client.models.generate_content(
                model=model,
                contents=contents,
                config=types.GenerateContentConfig(
                    max_output_tokens=req.max_tokens,
                    temperature=req.temperature,
                ),
            )
            text = response.text or ""
            usage = response.usage_metadata
            return LLMResponse(
                text=text,
                model=model,
                input_tokens=usage.prompt_token_count if usage else 0,
                output_tokens=usage.candidates_token_count if usage else 0,
            )
        except Exception as e:
            logger.error(f"Gemini error: {e}")
            raise LLMError(str(e)) from e