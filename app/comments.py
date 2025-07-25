from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class Comment(BaseModel):
    """
    表示一条评论信息。
    """
    comment_content: str = Field(..., description="用户发布的评论内容")
    uid: str = Field(..., description="评论在平台上的唯一标识 UID")
    user_name: Optional[str] = Field(default=None, description="评论发布者的昵称或用户名")
    comment_time: Optional[datetime] = Field(default=None, description="评论发布时间，格式为 yyyy-MM-dd HH:mm:ss")
    ip_address: Optional[str] = Field(default=None, description="用户的 IP 属地，如 '广东'、'北京'")
    response_count: Optional[int] = Field(default=None, description="该评论收到的回复数量")
    like_count: Optional[int] = Field(default=None, description="该评论获得的点赞数量")


class HighIntentComment(BaseModel):
    """
    表示一条被识别为高意向的评论及其理由。
    """
    comment_content: str = Field(..., description="用户发布的评论内容文本")
    reason: str = Field(..., description="判断该评论为高意向的理由说明")
    uid: str = Field(..., description="评论的唯一标识 UID")

class HighIntentCommentList(BaseModel):
    """
    表示一条被识别为高意向的评论及其理由。
    """
    high_intent_comment_list: List[HighIntentComment] = Field(..., description="高意向评论列表")
