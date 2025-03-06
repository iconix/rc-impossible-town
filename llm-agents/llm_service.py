import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any

# Import LLM providers
from ollama import chat as ollama_chat

try:
    from together import Together
except ImportError:
    Together = None


class LLMService:
    """Service to abstract different LLM providers"""

    def __init__(
        self,
        provider: str = "together",
        model_name: str = "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
        api_key: Optional[str] = None,
    ):
        """
        Initialize the LLM service

        Args:
            provider: The LLM provider to use (ollama or together)
            model_name: The model name to use
            api_key: API key for providers that require it (like Together)
        """
        self.configure(provider, model_name, api_key)

    def configure(self, provider: str, model_name: str, api_key: Optional[str] = None):
        """Configure the LLM service with provider and model"""
        self.provider = provider.lower()
        self.model_name = model_name
        self.api_key = api_key

        if self.provider == "together":
            if Together is None:
                raise ImportError(
                    "Failed to import Together. Make sure it's installed with 'pip install together'"
                )

            # Try to get API key from different sources
            final_api_key = self._get_api_key(api_key)
            if not final_api_key:
                raise ValueError(
                    "Together API key is required. Set it via TOGETHER_API_KEY environment variable, "
                    "pass it with --api-key, or add it to config.json"
                )

            # Set the environment variable for Together library
            os.environ["TOGETHER_API_KEY"] = final_api_key
            self.client = Together(api_key=final_api_key)
        elif self.provider == "ollama":
            self.client = None  # ollama doesn't need a client object
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

    def _get_api_key(self, provided_key: Optional[str] = None) -> Optional[str]:
        """
        Get API key from various sources in order of priority:
        1. Directly provided key
        2. Environment variable
        3. Config file
        """
        # Check if key was provided directly
        if provided_key:
            return provided_key

        # Check environment variable
        env_key = os.environ.get("TOGETHER_API_KEY")
        if env_key:
            return env_key

        # Check config file
        config_path = Path("config.json")
        if config_path.exists():
            try:
                with open(config_path, "r") as f:
                    config = json.load(f)
                    if "together_api_key" in config:
                        return config["together_api_key"]
            except (json.JSONDecodeError, IOError):
                pass

        return None

    def chat(
        self,
        messages: List[Dict[str, str]],
        format: Optional[Dict] = None,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """
        Send a chat request to the LLM provider

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            format: Optional JSON schema for response format (Ollama specific)
            temperature: Temperature parameter for generation

        Returns:
            Response from the LLM
        """
        if self.provider == "ollama":
            # Use Ollama's chat function
            kwargs = {}
            if format:
                kwargs["format"] = format

            response = ollama_chat(messages=messages, model=self.model_name, **kwargs)
            return response

        elif self.provider == "together":
            # Use Together's API
            kwargs = {}
            if format:
                kwargs["response_format"] = {
                    "type": "json_object",
                    "schema": format,
                }

            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "system", "content": "Only answer in JSON."}]
                + messages,
                temperature=temperature,
                **kwargs,
            )

            if format:
                # Clean up the markdown code block formatting and parse JSON
                msg_content = response.choices[0].message.content
                # Handle both markdown code blocks and language-prefixed JSON
                msg_content = (
                    msg_content.replace("```json", "")
                    .replace("```", "")
                    .replace("json\n", "")
                )
                msg_content = msg_content.strip()  # Remove any remaining whitespace

                try:
                    json.loads(msg_content)
                except json.JSONDecodeError as e:
                    raise ValueError(
                        f"Failed to parse JSON from response: {e}. Response: {msg_content}"
                    )
            else:
                msg_content = response.choices[0].message.content

            # Format response to match Ollama's structure
            return {
                "message": {"role": "assistant", "content": msg_content},
            }
