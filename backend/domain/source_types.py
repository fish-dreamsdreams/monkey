"""史料类型与分层规则。

职责：区分正史、史书、演义、传说与游戏设定，禁止把《三国演义》当作历史事实来源。
"""

from enum import Enum

from backend.core.exceptions import ValidationError


class SourceType(str, Enum):
    """来源类型。"""

    OFFICIAL_HISTORY = "official_history"
    HISTORICAL_BOOK = "historical_book"
    PAPER = "paper"
    ACADEMIC = "academic"
    TRADITION = "tradition"
    FOLKLORE = "folklore"
    LITERARY = "literary"
    GAME_SETTING = "game_setting"


class BoundLayer(str, Enum):
    """引文挂接的数据层。"""

    HISTORICAL = "historical"
    LITERARY = "literary"
    GAME = "game"


SOURCE_TYPE_LABELS_ZH: dict[SourceType, str] = {
    SourceType.OFFICIAL_HISTORY: "正史",
    SourceType.HISTORICAL_BOOK: "史书",
    SourceType.PAPER: "论文",
    SourceType.ACADEMIC: "学术资料",
    SourceType.TRADITION: "传统记载",
    SourceType.FOLKLORE: "民间传说",
    SourceType.LITERARY: "文学演义",
    SourceType.GAME_SETTING: "游戏设定",
}

FACT_SOURCE_TYPES: frozenset[SourceType] = frozenset(
    {
        SourceType.OFFICIAL_HISTORY,
        SourceType.HISTORICAL_BOOK,
        SourceType.PAPER,
        SourceType.ACADEMIC,
    }
)

SYSTEM_SOURCES: tuple[tuple[str, str, SourceType], ...] = (
    ("sanguozhi", "三国志", SourceType.OFFICIAL_HISTORY),
    ("houhanshu", "后汉书", SourceType.OFFICIAL_HISTORY),
    ("zizhitongjian", "资治通鉴", SourceType.HISTORICAL_BOOK),
    ("sanguoyanyi", "三国演义", SourceType.LITERARY),
    ("game_setting", "游戏设定", SourceType.GAME_SETTING),
)


def is_fact_eligible(source_type: SourceType) -> bool:
    """该类型是否有资格支撑 historical 史实栏。"""
    return source_type in FACT_SOURCE_TYPES


def validate_source_definition(name: str, source_type: SourceType) -> None:
    """校验来源定义：书名含「三国演义」时必须是文学演义。"""
    if "三国演义" in name.replace(" ", "") and source_type != SourceType.LITERARY:
        raise ValidationError(
            "《三国演义》必须标记为 literary（文学演义），不能当作正史或史书",
            field="source_type",
        )


def validate_citation_layer(source_type: SourceType, bound_layer: BoundLayer) -> None:
    """史实层只能引用正史/史书/论文/学术资料。"""
    if bound_layer == BoundLayer.HISTORICAL and source_type not in FACT_SOURCE_TYPES:
        raise ValidationError(
            "文学演义、民间传说、传统记载或游戏设定不能作为历史事实来源",
            field="bound_layer",
        )
