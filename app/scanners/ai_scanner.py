from fastapi import HTTPException, Depends
from anthropic import Anthropic
import openai, httpx, asyncio
from huggingface_hub import InferenceClient 
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.database import APIKey, get_db


async def send_request_to_provider(content: str, db: AsyncSession = Depends(get_db)) -> str:
    """
    Sends the populated template content to the appropriate API provider using the active API key.
    Supports Hugging Face, OpenAI, and Anthropic.
    """
    # Fetch the active API key
    query = select(APIKey).where(APIKey.is_active == True)
    result = await db.execute(query)
    active_key = result.scalar_one_or_none()

    if not active_key:
        raise HTTPException(status_code=400, detail="No active API key found")

    provider = active_key.provider.lower()
    api_key = active_key.token
    model = active_key.model
    max_tokens = active_key.max_tokens

    if provider == "huggingface":
        client = InferenceClient(api_key=api_key)
        messages = [{"role": "user", "content": content}]
        try:
            completion = await asyncio.to_thread(
                client.chat.completions.create,
                model=model,
                messages=messages,
                max_tokens=max_tokens
            )
            return completion.choices[0].message['content']
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Hugging Face API error: {str(e)}")

    elif provider == "openai":
        client = openai.Client(api_key=api_key)
        messages = [{"role": "user", "content": content}]
        try:
            completion = await asyncio.to_thread(
                client.chat.completions.create,
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=1
            )
            return completion.choices[0].message.content
        except httpx.HTTPError as e:
            raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")

    elif provider == "anthropic":
        client = Anthropic(api_key=api_key)
        messages = [{"role": "user", "content": content}]
        try:
            completion = await asyncio.to_thread(
                client.messages.create,
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=1
            )
            return completion.content[0].text
        except httpx.HTTPError as e:
            raise HTTPException(status_code=500, detail=f"Anthropic API error: {str(e)}")

    else:
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")

