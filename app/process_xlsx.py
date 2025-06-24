import json
import pandas as pd


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


def dict_to_json(data: dict, save_file_path: str) -> None:
    with open(save_file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("提取完成，共处理视频ID数：", len(data))

