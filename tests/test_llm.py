import asyncio

from agent.utils import load_llm_settings_from_toml
from agent.llm import LLM
from agent.data_format import Message

llm_settings = load_llm_settings_from_toml("agent/config.toml")
print(llm_settings)

llm = LLM(llm_settings)


async def test():
    messages = [Message.user_message("Hello, how are you?")]

    result = await llm.ask(messages)
    print(result)


if __name__ == "__main__":
    asyncio.run(test())