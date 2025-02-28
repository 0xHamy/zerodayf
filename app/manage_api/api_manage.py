from huggingface_hub import InferenceClient
import openai
from anthropic import Anthropic


def check_api(provider: str, token: str, model_name: str, max_tokens: int):
    """
    Returns a dict: {"valid": bool, "message": str}
    `valid` is True if the response from the model includes "19", else False.
    `message` provides success or failure info.
    """
    prompt = "What is result of 3 + 16? Return only the number."

    try:
        if provider.lower() == "huggingface":
            result_text = _check_huggingface(token, model_name, prompt, max_tokens)

        elif provider.lower() == "openai":
            result_text = _check_openai(token, model_name, prompt, max_tokens)
            
        elif provider.lower() == "anthropic":
            result_text = _check_anthropic(token, model_name, prompt, max_tokens)

        else:
            return {
                "valid": False,
                "message": f"Unknown provider: {provider}"
            }

        # Check if "19" is anywhere in the response (text, JSON, HTML, etc.)
        if "19" in result_text:
            return {
                "valid": True,
                "message": "API key is valid. The model responded with '19'."
            }
        else:
            truncated = result_text[:100] + ("..." if len(result_text) > 100 else "")
            return {
                "valid": False,
                "message": f"Response does not contain '19'. Got: {truncated}"
            }

    except Exception as e:
        return {
            "valid": False,
            "message": f"Error while checking API: {str(e)}"
        }


def _check_huggingface(token: str, model_name: str, prompt: str, max_tokens: int) -> str:
    client = InferenceClient(api_key=token)
    messages = [
        {"role": "user", "content": prompt}
    ]
    completion = client.chat.completions.create(
        model=model_name,
        messages=messages,
        max_tokens=max_tokens
    )
    return completion.choices[0].message.content


def _check_openai(token: str, model_name: str, prompt: str, max_tokens: int) -> str:
    client = openai.Client(api_key=token) 
    response = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=1
    )
    return response.choices[0].message.content


def _check_anthropic(token: str, model_name: str, prompt: str, max_tokens: int) -> str:
    client = Anthropic(api_key=token)
    message = client.messages.create(
        model=model_name,
        max_tokens=max_tokens,
        temperature=1,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return message.content[0].text



