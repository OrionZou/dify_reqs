import io
import base64
from enum import Enum
from PIL import Image
from typing import Any, List, Literal, Optional, Union, Dict

from pydantic import BaseModel, Field


def is_base64_uri(url: str) -> bool:
    return url.startswith("data:image/") and ";base64," in url


def encode_image(image: Union[str, Image.Image]):
    if isinstance(image, str):
        img = Image.open(image)
    else:
        img = image

    with io.BytesIO() as in_mem_file:
        img.save(in_mem_file, format="JPEG")
        in_mem_file.seek(0)
        img.close()
        return base64.b64encode(in_mem_file.read()).decode("utf-8")


def encode_image(image: Image.Image):
    with io.BytesIO() as in_mem_file:
        image.save(in_mem_file, format="JPEG")
        in_mem_file.seek(0)
        return base64.b64encode(in_mem_file.read()).decode("utf-8")


def image_to_base64(image: Image.Image, format: str = "PNG") -> str:
    """将 PIL.Image 转为 base64 字符串"""
    buffer = io.BytesIO()
    image.save(buffer, format=format)
    base64_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return base64_str


def base64_to_image(base64_str: str) -> Image.Image:
    # 如果是 data:image/jpeg;base64,... 开头，先去除头部
    if base64_str.startswith("data:image"):
        base64_str = base64_str.split(",", 1)[1]

    image_data = base64.b64decode(base64_str)
    buffer = io.BytesIO(image_data)
    buffer.seek(0)  # ✅ 重要！重置指针
    return Image.open(buffer)


def resize_and_crop_with_padding(image: Image.Image, patch_size: int = 512):
    width, height = image.size

    # 1. 缩放：短边到 patch_size，保持比例
    if width < height:
        new_width = patch_size
        new_height = int(height * patch_size / width)
    else:
        new_height = patch_size
        new_width = int(width * patch_size / height)

    image = image.resize((new_width, new_height), Image.LANCZOS)

    patches = []
    for top in range(0, new_height, patch_size):
        for left in range(0, new_width, patch_size):
            # 当前块的右下角
            right = left + patch_size
            bottom = top + patch_size

            # 裁剪实际区域（可能小于 patch_size）
            cropped = image.crop(
                (left, top, min(right, new_width), min(bottom, new_height)))

            # 创建黑色背景图
            patch = Image.new("RGB", (patch_size, patch_size), (0, 0, 0))
            patch.paste(cropped, (0, 0))
            patches.append(patch)

    return patches, image.size


class Role(str, Enum):
    """Message role options"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


ROLE_VALUES = tuple(role.value for role in Role)
ROLE_TYPE = Literal[ROLE_VALUES]  # type: ignore


class ToolChoice(str, Enum):
    """Tool choice options"""
    NONE = "none"
    AUTO = "auto"
    REQUIRED = "required"


TOOL_CHOICE_VALUES = tuple(choice.value for choice in ToolChoice)
TOOL_CHOICE_TYPE = Literal[TOOL_CHOICE_VALUES]  # type: ignore


class Function(BaseModel):
    name: str
    arguments: str


class ToolCall(BaseModel):
    """Represents a tool/function call in a message"""

    id: str
    type: str = "function"
    function: Function


class Message(BaseModel):
    """Represents a chat message in the conversation"""

    role: ROLE_TYPE = Field(...)  # type: ignore
    content: Optional[Union[str, List[Any]]] = Field(default=None)
    tool_calls: Optional[List[ToolCall]] = Field(default=None)
    name: Optional[str] = Field(default=None)
    tool_call_id: Optional[str] = Field(default=None)
    image_urls: Optional[List[str]] = Field(default=None)

    def __add__(self, other) -> List["Message"]:
        """支持 Message + list 或 Message + Message 的操作"""
        if isinstance(other, list):
            return [self] + other
        elif isinstance(other, Message):
            return [self, other]
        else:
            raise TypeError(
                f"unsupported operand type(s) for +: '{type(self).__name__}' and '{type(other).__name__}'"
            )

    def __radd__(self, other) -> List["Message"]:
        """支持 list + Message 的操作"""
        if isinstance(other, list):
            return other + [self]
        else:
            raise TypeError(
                f"unsupported operand type(s) for +: '{type(other).__name__}' and '{type(self).__name__}'"
            )

    def to_dict(self) -> dict:
        """Convert message to dictionary format"""
        message = {"role": self.role}
        if self.content is not None:
            message["content"] = self.content
        if self.tool_calls is not None:
            message["tool_calls"] = [
                tool_call.dict() for tool_call in self.tool_calls
            ]
        if self.name is not None:
            message["name"] = self.name
        if self.tool_call_id is not None:
            message["tool_call_id"] = self.tool_call_id
        return message

    @classmethod
    def user_message(
            cls,
            content: str,
            image_paths: Union[str, List[str], None] = None) -> "Message":
        """Create a user message"""
        content_list = []
        if image_paths is None:
            return cls(role=Role.USER, content=content)
        elif isinstance(image_paths, str):
            with Image.open(image_paths) as img:
                patch_dict = {
                    "type":
                    "image_url",
                    "image_url":
                    f"data:image/jpeg;base64,{image_to_base64(img,format='jpeg')}",
                }
            content_list.append(patch_dict)
        else:
            for image_path in image_paths:
                with Image.open(image_path) as img:
                    patchs, _ = resize_and_crop_with_padding(img)
                    for patch in patchs:
                        patch_dict = {
                            "type": "image_url",
                            "image_url": {
                                "url":
                                f"data:image/jpeg;base64,{image_to_base64(patch, format='jpeg')}",
                                # "detail": "high",
                            }
                        }
                        content_list.append(patch_dict)
        content_list.append({"type": "text", "text": content})

        return cls(role=Role.USER, content=content_list)

    @classmethod
    def system_message(cls, content: str) -> "Message":
        """Create a system message"""
        return cls(role=Role.SYSTEM, content=content)

    @classmethod
    def assistant_message(cls, content: Optional[str] = None) -> "Message":
        """Create an assistant message"""
        return cls(role=Role.ASSISTANT, content=content)

    @classmethod
    def tool_message(cls, content: str, name, tool_call_id: str) -> "Message":
        """Create a tool message"""
        return cls(role=Role.TOOL,
                   content=content,
                   name=name,
                   tool_call_id=tool_call_id)

    @classmethod
    def from_tool_calls(cls,
                        tool_calls: List[Any],
                        content: Union[str, List[str]] = "",
                        **kwargs):
        """Create ToolCallsMessage from raw tool calls.

        Args:
            tool_calls: Raw tool calls from LLM
            content: Optional message content
        """
        formatted_calls = [{
            "id": call.id,
            "function": call.function.model_dump(),
            "type": "function"
        } for call in tool_calls]
        return cls(role=Role.ASSISTANT,
                   content=content,
                   tool_calls=formatted_calls,
                   **kwargs)
