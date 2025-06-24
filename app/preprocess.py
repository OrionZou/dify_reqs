
import re

def is_valid_uid(uid: str) -> bool:
    """
    检测 UID 是否有效。
    
    有效 UID 的规则：
    - 是字符串类型
    - 仅包含数字
    - 长度在 8~64 位之间
    - 不能是全 0 或重复数字
    - 不包含空格或特殊字符
    """
    if not isinstance(uid, str):
        return False

    uid = uid.strip()

    if not re.fullmatch(r'\d{8,64}', uid):
        return False

    if len(set(uid)) == 1:  # 如 "000000", "111111"
        return False

    return True