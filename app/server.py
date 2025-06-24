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
