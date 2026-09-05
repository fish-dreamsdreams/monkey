"""剧情图领域规则。

职责：定义节点类型，并检测无条件环。条件回边必须带终止条件。不执行对白或战斗。
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from enum import Enum

from backend.core.exceptions import ValidationError


class StoryNodeType(str, Enum):
    """剧情节点类型。效果只是数据，编辑器不驱动游戏。"""

    DIALOGUE = "dialogue"
    HISTORICAL_EVENT = "historical_event"
    BATTLE = "battle"
    QUEST = "quest"
    CHARACTER_JOIN = "character_join"
    CHARACTER_LEAVE = "character_leave"
    CITY_CAPTURE = "city_capture"
    FACTION_CREATE = "faction_create"
    FACTION_DESTROY = "faction_destroy"
    CHOICE = "choice"
    CONDITION = "condition"
    REWARD = "reward"


STORY_NODE_TYPE_LABELS_ZH: dict[StoryNodeType, str] = {
    StoryNodeType.DIALOGUE: "对白",
    StoryNodeType.HISTORICAL_EVENT: "历史事件",
    StoryNodeType.BATTLE: "战役演出",
    StoryNodeType.QUEST: "任务",
    StoryNodeType.CHARACTER_JOIN: "人物加入",
    StoryNodeType.CHARACTER_LEAVE: "人物离开",
    StoryNodeType.CITY_CAPTURE: "城池易主",
    StoryNodeType.FACTION_CREATE: "势力成立",
    StoryNodeType.FACTION_DESTROY: "势力灭亡",
    StoryNodeType.CHOICE: "选项",
    StoryNodeType.CONDITION: "条件",
    StoryNodeType.REWARD: "奖励",
}


class StoryConditionType(str, Enum):
    """节点条件。只存储，不求值。"""

    FLAG = "flag"
    YEAR_AT_LEAST = "year_at_least"
    HAS_CHARACTER = "has_character"
    CUSTOM = "custom"


STORY_CONDITION_TYPE_LABELS_ZH: dict[StoryConditionType, str] = {
    StoryConditionType.FLAG: "标记",
    StoryConditionType.YEAR_AT_LEAST: "不早于某年",
    StoryConditionType.HAS_CHARACTER: "拥有人物",
    StoryConditionType.CUSTOM: "自定义",
}


class StoryActionType(str, Enum):
    """节点动作。只存储，不执行。"""

    SET_FLAG = "set_flag"
    GRANT_NOTE = "grant_note"
    CUSTOM = "custom"


STORY_ACTION_TYPE_LABELS_ZH: dict[StoryActionType, str] = {
    StoryActionType.SET_FLAG: "设置标记",
    StoryActionType.GRANT_NOTE: "发放说明",
    StoryActionType.CUSTOM: "自定义",
}


class StoryCastRole(str, Enum):
    """节点出场人物角色。"""

    SPEAKER = "speaker"
    PRESENT = "present"
    MENTIONED = "mentioned"


STORY_CAST_ROLE_LABELS_ZH: dict[StoryCastRole, str] = {
    StoryCastRole.SPEAKER: "说话人",
    StoryCastRole.PRESENT: "在场",
    StoryCastRole.MENTIONED: "提及",
}


@dataclass(frozen=True)
class GraphNode:
    """环检测用的节点摘要。"""

    id: str
    is_entry: bool
    is_ending: bool


@dataclass(frozen=True)
class GraphEdge:
    """环检测用的有向边。has_terminator 表示条件回边已写终止条件。"""

    from_id: str
    to_id: str
    is_conditional: bool
    has_terminator: bool


@dataclass(frozen=True)
class GraphReport:
    """剧情图校验结果。草稿允许 incomplete，但不能有无条件环。"""

    valid: bool
    errors: tuple[str, ...]
    has_unconditional_cycle: bool
    entry_reaches_ending: bool
    entry_count: int
    ending_count: int


def validate_conditional_terminator(*, is_conditional: bool, condition_note: str | None) -> None:
    """条件回边必须填写终止条件说明。"""
    if is_conditional and not (condition_note and condition_note.strip()):
        raise ValidationError("条件回边必须填写终止条件", field="condition_note")


def has_unconditional_cycle(node_ids: set[str], edges: list[GraphEdge]) -> bool:
    """无条件边是否构成有向环（含自环）。"""
    graph: dict[str, list[str]] = {node_id: [] for node_id in node_ids}
    for edge in edges:
        if edge.is_conditional:
            continue
        graph.setdefault(edge.from_id, []).append(edge.to_id)
        graph.setdefault(edge.to_id, [])

    white, gray, black = 0, 1, 2
    color = {node_id: white for node_id in graph}

    def dfs(node_id: str) -> bool:
        color[node_id] = gray
        for nxt in graph[node_id]:
            state = color.get(nxt, white)
            if state == gray:
                return True
            if state == white and dfs(nxt):
                return True
        color[node_id] = black
        return False

    return any(dfs(node_id) for node_id, state in list(color.items()) if state == white)


def assert_edge_allowed(node_ids: set[str], edges: list[GraphEdge], new_edge: GraphEdge) -> None:
    """新增边时立即拒绝无条件环和缺终止条件的条件边。"""
    validate_conditional_terminator(
        is_conditional=new_edge.is_conditional,
        condition_note="yes" if new_edge.has_terminator else None,
    )
    if new_edge.from_id not in node_ids or new_edge.to_id not in node_ids:
        raise ValidationError("边的两端必须属于同一剧情", field="to_node_id")
    if not new_edge.is_conditional and has_unconditional_cycle(node_ids, [*edges, new_edge]):
        raise ValidationError("无条件边形成环；只允许带终止条件的回边", field="to_node_id")


def analyze_story_graph(nodes: list[GraphNode], edges: list[GraphEdge]) -> GraphReport:
    """完整图校验：入口、结束可达、无条件无环、条件边有终止条件。"""
    errors: list[str] = []
    node_ids = {node.id for node in nodes}
    entries = [node for node in nodes if node.is_entry]
    endings = {node.id for node in nodes if node.is_ending}
    cycle = has_unconditional_cycle(node_ids, edges) if node_ids else False
    if cycle:
        errors.append("无条件边形成环；只允许带终止条件的回边")
    for edge in edges:
        if edge.is_conditional and not edge.has_terminator:
            errors.append("条件回边必须填写终止条件")
            break
    if len(entries) != 1:
        errors.append("剧情必须恰好有一个入口节点")
    if not endings:
        errors.append("剧情至少需要一个结束节点")
    reaches = _entry_reaches_ending(entries, endings, edges) if len(entries) == 1 and endings else False
    if len(entries) == 1 and endings and not reaches:
        errors.append("无法从入口到达结束节点")
    unique_errors = tuple(dict.fromkeys(errors))
    return GraphReport(
        valid=not unique_errors,
        errors=unique_errors,
        has_unconditional_cycle=cycle,
        entry_reaches_ending=reaches,
        entry_count=len(entries),
        ending_count=len(endings),
    )


def validate_node_reference(node_type: StoryNodeType, *, event_id: str | None, character_id: str | None, city_id: str | None, faction_id: str | None) -> None:
    """按节点类型检查必填引用。引用存在性由应用服务查库。"""
    if node_type == StoryNodeType.HISTORICAL_EVENT and not event_id:
        raise ValidationError("历史事件节点必须引用事件", field="event_id")
    if node_type in {StoryNodeType.CHARACTER_JOIN, StoryNodeType.CHARACTER_LEAVE} and not character_id:
        raise ValidationError("人物加入/离开节点必须引用人物", field="character_id")
    if node_type == StoryNodeType.CITY_CAPTURE and not city_id:
        raise ValidationError("城池易主节点必须引用城池", field="city_id")
    if node_type in {StoryNodeType.FACTION_CREATE, StoryNodeType.FACTION_DESTROY} and not faction_id:
        raise ValidationError("势力节点必须引用势力", field="faction_id")


def _entry_reaches_ending(entries: list[GraphNode], endings: set[str], edges: list[GraphEdge]) -> bool:
    graph: dict[str, list[str]] = defaultdict(list)
    for edge in edges:
        graph[edge.from_id].append(edge.to_id)
    start = entries[0].id
    seen: set[str] = set()
    stack = [start]
    while stack:
        current = stack.pop()
        if current in seen:
            continue
        seen.add(current)
        if current in endings:
            return True
        stack.extend(graph[current])
    return False
