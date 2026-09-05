"""预置性格标签。

职责：提供可扩展的系统性格代码，不把性格写死为一段描述文本。
"""

SYSTEM_PERSONALITY_TAGS: tuple[tuple[str, str], ...] = (
    ("brave", "勇猛"),
    ("cautious", "谨慎"),
    ("suspicious", "多疑"),
    ("loyal", "忠诚"),
    ("decisive", "果断"),
    ("benevolent", "仁厚"),
    ("cunning", "狡诈"),
    ("ambitious", "野心"),
    ("calm", "冷静"),
)
