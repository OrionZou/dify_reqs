import json
import asyncio
from loguru import logger

from app.process_xlsx import extract_comments_by_video_id
from app.comments import High_Intent_Comment
from app.prompts import SYSTEM_PROMPT_TEMPL, USER_PROMPT_TEMPL
from app.preprocess import is_valid_uid
from agent.utils import load_llm_settings_from_toml
from agent.llm import LLM
from agent.data_format import Message


async def main():
    file_path = "output.xlsx"  # 请根据实际路径修改
    data = extract_comments_by_video_id(file_path)
    llm_settings = load_llm_settings_from_toml("agent/config.toml")
    llm = LLM(llm_settings)
    for k, v in data.items():
        vedio_id = v["vedio_id"]
        vedio_info = f'行业: {v["industry"]} 关键字: {v["keyword"]}'
        comment_list = v["comment_list"]
        print(f"评论数：{len(comment_list)}")
        comment_list_str = json.dumps(comment_list, ensure_ascii=False, indent=2)
        # print(comment_list_str)
        messages = [Message.user_message(
            USER_PROMPT_TEMPL.render(vedio_info=vedio_info,
                                     comment_list=comment_list_str))]
        response = await llm.ask_structure_output(messages=messages,
                                 response_format=High_Intent_Comment,
                                 system_msgs=[Message.system_message(
                                     SYSTEM_PROMPT_TEMPL.render())])
        logger.info(response)
        if is_valid_uid(response.uid):
            


if __name__ == "__main__":
    asyncio.run(main())
