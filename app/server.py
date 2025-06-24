from fastapi import FastAPI, Body
from pydantic import BaseModel, Field
from typing import List
from datetime import datetime

from app.comments import Comment
from app.offline_main import get_high_intent_commemts
from agent.utils import load_llm_settings_from_toml
from agent.llm import LLM
from agent.data_format import Message

llm_settings = load_llm_settings_from_toml("agent/config.toml")
llm = LLM(llm_settings)
app = FastAPI()

# ---- 引入你已有的模型 ----

# class Comment(BaseModel):
#     comment_content: str = Field(..., description="用户发布的评论内容")
#     uid: str = Field(..., description="评论在平台上的唯一标识 UID")
#     user_name: str | None = Field(None, description="评论发布者的昵称或用户名")
#     comment_time: datetime | None = Field(None, description="评论发布时间")
#     ip_address: str | None = Field(None, description="IP 属地")
#     response_count: int | None = Field(None, description="评论回复数")
#     like_count: int | None = Field(None, description="评论点赞数")

# class HighIntentComment(BaseModel):
#     comment_content: str = Field(..., description="高意向评论内容")
#     reason: str = Field(..., description="判断为高意向的原因")
#     uid: str = Field(..., description="用户 UID")

# class HighIntentCommentList(BaseModel):
#     high_intent_comment_list: List[HighIntentComment]

class HighIntentRequest(BaseModel):
    vedio_info: str
    comment_list: List[dict]
    high_intent_comment_num: int = Field(
        5, gt=0, description="希望返回的高意向评论数量，默认为 5"
    )

# ---- FastAPI 路由封装 ----

@app.post("/get_high_intent_comments", response_model=List[Comment])
async def get_high_intent_comments_api(req: HighIntentRequest = Body(...)):
    result = await get_high_intent_commemts(
        vedio_info=req.vedio_info,
        comment_list=req.comment_list,
        high_intent_comment_num=req.high_intent_comment_num
    )
    return result
