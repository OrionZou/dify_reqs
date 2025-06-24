import json
import pandas as pd

import time
import argparse
import requests
import asyncio
from loguru import logger




def extract_comments_by_video_id(file_path: str) -> dict:
    df = pd.read_excel(file_path)

    result = {}

    for _, row in df.iterrows():
        video_id = str(row['视频ID'])
        vedeo_info ={
            "vedio_id": video_id,
            "industry": row["行业"],
            "keyword": row["关键字"]
        }
        comment_info = {
            "comment_content": row['评论内容'],
            # "user_name": row['用户名称'],
            "comment_time": str(row['创建时间']),
            "ip_address": row['IP未知'],
            "response_count": int(row['回复数']),
            "like_count": int(row['点赞数']),
            "uid": str(row['UID'])
        }
        if video_id not in result:
            result[video_id] = vedeo_info
            result[video_id]["comment_list"] = [comment_info]
        else:
            result[video_id]["comment_list"].append(comment_info)

    return result

def preprocess(comment_list):
    filtered_data = []
    for comment in comment_list:
        if isinstance(comment["comment_content"], str) and comment["comment_content"].strip() != "":
            filtered_data.append(comment)
    return filtered_data


async def demo(args):
    file_path = args.file_path
    data = extract_comments_by_video_id(file_path)

    for vedio_id, v in data.items():
        start_time = time.time()
        vedio_info = f'行业: {v["industry"]} 关键字: {v["keyword"]}'
        comment_list = v["comment_list"]

        before_comment_len = len(comment_list)
        comment_list = preprocess(comment_list)
        logger.info(
            f"过滤前评论数：{(before_comment_len)} 过滤后评论数：{len(comment_list)}")

        # 设置请求头
        headers = {"Content-Type": "application/json"}

        # 构造请求体
        payload = {
            "vedio_info": vedio_info,
            "comment_list": comment_list,
            "high_intent_comment_num": args.high_intent_comment_num
        }
        # 发送 POST 请求
        response = requests.post(args.url, json=payload, headers=headers)

        # 打印响应结果
        if response.status_code == 200:
            print(f"视频{vedio_id} 成功获取高意向评论：")
            print(response.json())
        else:
            print(f"请求失败，状态码：{response.status_code}")
            print(response.text)

        logger.info(f"finish time: {round(time.time()-start_time,4)}s")


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
    parser.add_argument("--url",
                        type=str,
                        default="http://127.0.0.1:8000/get_high_intent_comments",
                        help="高意向请求 url")
    args = parser.parse_args()

    asyncio.run(demo(args))
