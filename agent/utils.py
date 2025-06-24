from agent.llm import LLMSettings
import toml

def load_llm_settings_from_toml(file_path: str) -> LLMSettings:
    """
    从 config.toml 文件加载 LLMSettings 实例。

    :param file_path: config.toml 文件路径
    :return: LLMSettings 实例
    """
    config = toml.load(file_path)
    llm_config = config.get("llm", {})
    
    return LLMSettings(
        model=llm_config.get("model", ""),
        base_url=llm_config.get("base_url", ""),
        api_key=llm_config.get("api_key", ""),
        max_tokens=llm_config.get("max_tokens", 4096),
        temperature=llm_config.get("temperature", 1.0),
        api_type="",  # config.toml 中未定义，需手动设置或扩展
        api_version=""  # config.toml 中未定义，需手动设置或扩展
    )