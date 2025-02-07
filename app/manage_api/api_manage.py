import requests
from huggingface_hub import InferenceClient
from openai import OpenAI


def check_api(provider: str, token: str, model_name: str):
    """
    Returns a dict: {"valid": bool, "message": str}
    `valid` is True if the response from the model includes "19", else False.
    `message` provides success or failure info.
    """
    prompt = "What is result of 3 + 16? Return only the number."

    try:
        if provider.lower() == "huggingface":
            result_text = _check_huggingface(token, model_name, prompt)

        elif provider.lower() == "openai":
            result_text = _check_openai(token, model_name, prompt)

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


def _check_huggingface(token: str, model_name: str, prompt: str) -> str:
    client = InferenceClient(api_key=token)
    messages = [
        {"role": "user", "content": prompt}
    ]
    completion = client.chat.completions.create(
        model=model_name,
        messages=messages,
        max_tokens=100
    )
    return completion.choices[0].message.content


def _check_openai(token: str, model_name: str, prompt: str) -> str:
    
    client = OpenAI(api_key=token)
    messages = [
        {"role": "user", "content": prompt}
    ]
    completion = client.chat.completions.create(
        model=model_name,
        messages=messages,
        max_tokens=100
    )
    return completion.choices[0].message.content
