
# LLM Module Documentation

This module contains all the files responsible for communicating with Large Language Models (LLMs) such as Gemini and Groq.

---

# `gemini_provider.py`

This file handles communication with the Gemini AI model.

## Purpose

A simple request-response flow occurs with Gemini AI:

1. Receive an `LLMRequest`
2. Build the prompt/messages
3. Send the request to Gemini
4. Receive the response
5. Return an `LLMResponse`

---

## Gemini Client Initialization

```python
def __init__(self):
    self._client = genai.Client(
        api_key=settings.gemini_api_key
    )
```

### Explanation

This constructor initializes the Gemini client using the API key.

After initialization, the application can access Gemini functionality through:

```python
self._client
```

---

## Chat History Storage

```python
contents = []
```

The `contents` list stores the conversation history that is sent to Gemini.

Example:

```text
User: You are a stock analyst.
Model: Understood.
User: Analyze Tesla stock.
```

---

## Temperature

Temperature controls how random or creative the AI responses are.

| Temperature | Behavior                                         |
| ----------- | ------------------------------------------------ |
| 0.0         | Very deterministic, picks the most likely answer |
| 0.2         | Focused, consistent, less variation              |
| 0.5         | Balanced                                         |
| 0.7         | Natural and slightly creative                    |
| 1.0         | More diverse and creative                        |
| 1.5+        | Very random, can become less reliable            |

---

## Model Used

```text
gemini-2.0-flash
```

---

## Request Flow

```text
API Request
     │
     ▼
LLMRequest
     │
     ▼
GeminiProvider.complete()
     │
     ▼
Build Messages
     │
     ▼
Gemini API
     │
     ▼
Response
     │
     ▼
LLMResponse
     │
     ▼
Return to Service Layer
```

---

# `groq_provider.py`

This file handles communication with Groq-hosted LLMs.

---

## Purpose

Architecturally, it performs the same job as the Gemini provider.

Both providers:

* Receive an `LLMRequest`
* Build a prompt/message format
* Send the request to an LLM
* Get the response
* Extract token usage
* Return an `LLMResponse`
* Convert provider-specific errors into `LLMError`

---

## Default Model

```text
llama-3.3-70b-versatile
```

---

## Request Flow

```text
LLMRequest
     │
     ▼
GroqProvider
     │
     ▼
Llama/Mixtral Model on Groq
     │
     ▼
LLMResponse
```

---

## Key Difference from Gemini

Groq supports a native system role:

```python
{
    "role": "system",
    "content": req.system
}
```

while the Gemini implementation simulates a system prompt through conversation messages.

---

# `gateway.py`

The gateway acts as the single entry point for all LLM providers.

---

## Purpose

The gateway creates provider objects and routes requests to the selected provider.

```python
self._gemini = GeminiProvider()
self._groq = GroqProvider()
```

Although both providers are initialized, only one provider is used per request.

---

## Architecture

```text
API
 │
 ▼
Service Layer
 │
 ▼
LLMGateway
 │
 ├── GeminiProvider
 │
 └── GroqProvider
```

---

## Routing Logic

The gateway checks the configured provider:

```python
if self._provider == "groq":
    return await self._groq.complete(req)

return await self._gemini.complete(req)
```

### Example

If the provider is:

```text
groq
```

then:

```text
Request
   │
   ▼
LLMGateway
   │
   ▼
GroqProvider
   │
   ▼
Groq API
```

If the provider is:

```text
gemini
```

then:

```text
Request
   │
   ▼
LLMGateway
   │
   ▼
GeminiProvider
   │
   ▼
Gemini API
```

---

## Benefits

This is a common production pattern because it provides a single abstraction layer for all LLM providers.

The rest of the application never directly communicates with Gemini or Groq.

Instead, it communicates only with:

```python
LLMGateway
```

The gateway's responsibility is:

> Given a request, decide which LLM provider should handle it and forward the request there.

This makes it easy to add additional providers in the future such as:

* OpenAI
* Claude
* DeepSeek
* Mistral

without changing the service layer.
