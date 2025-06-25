import json
from loguru import logger
from typing import Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field

from openai import (APIError, AsyncOpenAI, AuthenticationError, OpenAIError,
                    RateLimitError, AsyncAzureOpenAI)
from tenacity import retry, stop_after_attempt, wait_random_exponential
from agent.data_format import Message

class LLMSettings(BaseModel):
    model: str = Field(..., description="Model name")
    base_url: str = Field(..., description="API base URL")
    api_key: str = Field(..., description="API key")
    max_tokens: int = Field(4096,
                            description="Maximum number of tokens per request")
    temperature: float = Field(1.0, description="Sampling temperature")
    api_type: str = Field(..., description="AzureOpenai or Openai")
    api_version: str = Field(...,
                             description="Azure Openai version if AzureOpenai")

class LLM:

    def __init__(self,
                 llm_config: LLMSettings):
        if not hasattr(self,
                       "client"):  # Only initialize if not already initialized
            self.model = llm_config.model
            self.max_tokens = llm_config.max_tokens
            self.temperature = llm_config.temperature
            self.api_type = llm_config.api_type
            self.api_key = llm_config.api_key
            self.api_version = llm_config.api_version
            self.base_url = llm_config.base_url
            if self.api_type == "azure":
                self.client = AsyncAzureOpenAI(azure_endpoint=self.base_url,
                                               api_key=self.api_key,
                                               api_version=self.api_version)
            else:
                self.client = AsyncOpenAI(api_key=self.api_key,
                                          base_url=self.base_url)

    @staticmethod
    def format_messages(messages: List[Union[dict, Message]]) -> List[dict]:
        """
        Format messages for LLM by converting them to OpenAI message format.

        Args:
            messages: List of messages that can be either dict or Message objects

        Returns:
            List[dict]: List of formatted messages in OpenAI format

        Raises:
            ValueError: If messages are invalid or missing required fields
            TypeError: If unsupported message types are provided

        Examples:
            >>> msgs = [
            ...     Message.system_message("You are a helpful assistant"),
            ...     {"role": "user", "content": "Hello"},
            ...     Message.user_message("How are you?")
            ... ]
            >>> formatted = LLM.format_messages(msgs)
        """
        formatted_messages = []
        for message in messages:
            if isinstance(message, dict):
                # If message is already a dict, ensure it has required fields
                if "role" not in message:
                    raise ValueError("Message dict must contain 'role' field")
                formatted_messages.append(message)
            elif isinstance(message, Message):
                # If message is a Message object, convert it to dict
                formatted_messages.append(message.to_dict())
            else:
                raise TypeError(f"Unsupported message type: {type(message)}")

        # Validate all messages have required fields
        for msg in formatted_messages:
            if msg["role"] not in ["system", "user", "assistant", "tool"]:
                raise ValueError(f"Invalid role: {msg['role']}")
            if "content" not in msg and "tool_calls" not in msg:
                raise ValueError(
                    "Message must contain either 'content' or 'tool_calls'")

        return formatted_messages

    @retry(
        wait=wait_random_exponential(min=1, max=60),
        stop=stop_after_attempt(6),
    )
    async def ask(
        self,
        messages: List[Union[dict, Message]],
        system_msgs: Optional[List[Union[dict, Message]]] = None,
        stream: bool = True,
        temperature: Optional[float] = None,
    ) -> str:
        """
        Send a prompt to the LLM and get the response.

        Args:
            messages: List of conversation messages
            system_msgs: Optional system messages to prepend
            stream (bool): Whether to stream the response
            temperature (float): Sampling temperature for the response

        Returns:
            str: The generated response

        Raises:
            ValueError: If messages are invalid or response is empty
            OpenAIError: If API call fails after retries
            Exception: For unexpected errors
        """
        try:
            # Format system and user messages
            if system_msgs:
                system_msgs = self.format_messages(system_msgs)
                messages = system_msgs + self.format_messages(messages)
            else:
                messages = self.format_messages(messages)
            if not stream:
                # Non-streaming request
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=self.max_tokens,
                    temperature=temperature or self.temperature,
                    stream=False,
                )
                if not response.choices or not response.choices[
                        0].message.content:
                    raise ValueError("Empty or invalid response from LLM")
                return response.choices[0].message.content
            # Streaming request
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=temperature or self.temperature,
                stream=True,
            )

            collected_messages = []
            async for chunk in response:
                chunk_message = chunk.choices[0].delta.content or ""
                collected_messages.append(chunk_message)
                print(chunk_message, end="", flush=True)

            print()  # Newline after streaming
            full_response = "".join(collected_messages).strip()
            if not full_response:
                raise ValueError("Empty response from streaming LLM")
            return full_response

        except ValueError as ve:
            logger.error(f"Validation error: {ve}")
            raise
        except OpenAIError as oe:
            logger.error(f"OpenAI API error: {oe}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in ask: {e}")
            raise

    async def ask_structure_output(
        self,
        messages: List[Union[dict, Message]],
        response_format: BaseModel,
        system_msgs: Optional[List[Union[dict, Message]]] = None,
        temperature: Optional[float] = None,
        stream: bool = False,
        enable_thinking: bool = False,
    ) -> BaseModel:
        """
        Send a prompt to the LLM  and parse the response into the specified structured output.

        Args:
            messages: List of conversation messages
            response_format: pydantic basemodel class
            system_msgs: Optional system messages to prepend
            stream (bool): Whether to stream the response
            temperature (float): Sampling temperature for the response

        Returns:
            BaseModel: pydantic basemodel class

        Raises:
            ValueError: If messages are invalid or response is empty
            OpenAIError: If API call fails after retries
            Exception: For unexpected errors
        """
        response_format_prompt = f"""
        输入的 json schema内容如下:
        {response_format.model_json_schema()}
        """
        try:
            # Format system and user messages
            formatted_messages = (self.format_messages(system_msgs) +
                                  self.format_messages(messages) if system_msgs
                                  else self.format_messages(messages))
            formatted_messages[-1]['content'] += response_format_prompt
            # Make API request without streaming
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=formatted_messages,
                max_tokens=self.max_tokens,
                temperature=temperature or self.temperature,
                response_format={"type": "json_object"},
                stream = stream,
                extra_body={"enable_thinking": enable_thinking}
            )
            response_str = response.choices[0].message.content
            print(response_str)
            response_json = json.loads(response_str)

            structured_output = response_format(**response_json)
            if not structured_output:
                raise ValueError("Empty response from LLM")
            return structured_output
        except json.JSONDecodeError as je:
            logger.error(f"JSONDecode error: {je}")
            raise
        except ValueError as ve:
            logger.error(f"Value error: {ve}")
            raise
        except OpenAIError as oe:
            logger.error(f"OpenAI API error: {oe}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise
