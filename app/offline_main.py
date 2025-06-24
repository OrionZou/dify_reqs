import json
import asyncio
import argparse

from loguru import logger

from app.process_xlsx import extract_comments_by_video_id
from app.comments import Comment, HighIntentCommentList
from app.prompts import SYSTEM_PROMPT_TEMPL, USER_PROMPT_TEMPL
from app.preprocess import is_valid_uid, preprocess
from agent.utils import load_llm_settings_from_toml
from agent.llm import LLM
from agent.data_format import Message


async def main(args):
    file_path = args.file_path
    data = extract_comments_by_video_id(file_path)
    llm_settings = load_llm_settings_from_toml("agent/config.toml")
    llm = LLM(llm_settings)

    for k, v in data.items():
        vedio_id = v["vedio_id"]
        vedio_info = f'行业: {v["industry"]} 关键字: {v["keyword"]}'
        comment_list = v["comment_list"]
        before_comment_len = len(comment_list)
        comment_list = preprocess(comment_list)
        print(f"过滤前评论数：{(before_comment_len)} 过滤后评论数：{len(comment_list)}")
        # print(f"前 5 条评论：{comment_list[:5]}")
        comment_list_str = json.dumps(comment_list,
                                      ensure_ascii=False,
                                      indent=2)
        # print(comment_list_str)
        comment_dict = {}
        for comment in comment_list:
            comment_dict[comment['uid']] = Comment(**comment)
        messages = [
            Message.user_message(
                USER_PROMPT_TEMPL.render(vedio_info=vedio_info,
                                         comment_list=comment_list_str))
        ]

        high_intent_comment_num = min(args.high_intent_comment_num,
                                      int(0.5 * len(comment_list)))
        if high_intent_comment_num <= 0:
            logger.error(f"comment is too few")
            return
        try:
            response = await llm.ask_structure_output(
                messages=messages,
                response_format=HighIntentCommentList,
                system_msgs=[
                    Message.system_message(
                        SYSTEM_PROMPT_TEMPL.render(
                            high_intent_comment_num=high_intent_comment_num))
                ])

            result = []
            for high_intent_comment in response.high_intent_comment_list:
                if is_valid_uid(high_intent_comment.uid):
                    if high_intent_comment.uid not in comment_dict.keys():
                        logger.warning(
                            f"high_intent_comment is unvalid: {high_intent_comment}"
                        )
                    else:
                        result.append(comment_dict[high_intent_comment.uid])
                else:
                    logger.warning(
                        f"high_intent_comment is unvalid: {high_intent_comment}"
                    )
            for data in result:
                logger.info(data.json())
            return result
        except Exception as e:
            logger.error(f"Error:{e}")


if __name__ == "__main__":
    # 使用 argparse 解析命令行参数
    parser = argparse.ArgumentParser(description="处理 Excel 文件并生成评论分析")
    parser.add_argument("--file_path",
                        type=str,
                        default="./demo_data/output.xlsx",
                        help="Excel 文件路径")
    parser.add_argument("--high_intent_comment_num",
                        type=int,
                        default=5,
                        help="高意向评论条数")
    args = parser.parse_args()

    asyncio.run(main(args))
