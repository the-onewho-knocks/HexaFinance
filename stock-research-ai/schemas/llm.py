from typing import Optional

from pydantic import BaseModel


class LLMRequest(BaseModel):
    prompt: str
    system: Optional[str] = None
    model: Optional[str] = None
    max_tokens: int = 4096
    temperature: float = 0.3


class LLMResponse(BaseModel):
    text: str
    model: str
    input_tokens: int
    output_tokens: int