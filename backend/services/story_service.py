"""剧情应用服务。

职责：维护叙事节点图。无条件边禁止成环；条件回边必须带终止条件。不执行剧情或战斗。
"""

from backend.core.exceptions import ConflictError, NotFoundError, ValidationError
from backend.core.ids import EntityPrefix, new_id, require_id
from backend.domain.source_types import BoundLayer
from backend.domain.story_rules import (
    GraphEdge,
    GraphNode,
    StoryActionType,
    StoryCastRole,
    StoryConditionType,
    StoryNodeType,
    analyze_story_graph,
    assert_edge_allowed,
    validate_conditional_terminator,
    validate_node_reference,
)
from backend.models.story import (
    Story,
    StoryAction,
    StoryChapter,
    StoryChoice,
    StoryCondition,
    StoryEdge,
    StoryNode,
    StoryNodeCharacter,
)
from backend.repositories.character_repository import CharacterRepository
from backend.repositories.city_repository import CityRepository
from backend.repositories.event_repository import EventRepository
from backend.repositories.faction_repository import FactionRepository
from backend.repositories.project_repository import ProjectRepository
from backend.repositories.story_repository import StoryRepository
from backend.schemas.city import CityRef, FactionRef
from backend.schemas.relationship import CharacterRef
from backend.schemas.story import (
    EventRef,
    StoryActionRead,
    StoryActionWrite,
    StoryCastRead,
    StoryCastWrite,
    StoryChapterRead,
    StoryChapterWrite,
    StoryChoiceRead,
    StoryChoiceWrite,
    StoryConditionRead,
    StoryConditionWrite,
    StoryEdgeRead,
    StoryEdgeWrite,
    StoryGraphRead,
    StoryNodeRead,
    StoryNodeWrite,
    StoryRead,
    StorySummary,
    StoryWrite,
)


class StoryService:
    """剧情用例编排。"""

    def __init__(
        self,
        stories: StoryRepository,
        characters: CharacterRepository,
        cities: CityRepository,
        factions: FactionRepository,
        events: EventRepository,
        projects: ProjectRepository,
    ) -> None:
        self._stories = stories
        self._characters = characters
        self._cities = cities
        self._factions = factions
        self._events = events
        self._projects = projects

    async def create(self, project_id: str, payload: StoryWrite) -> StoryRead:
        """创建空剧情。"""
        await self._require_project(project_id)
        self._assert_narrative_layer(payload.layer)
        if await self._stories.get_by_code(project_id, payload.code) is not None:
            raise ConflictError(f"剧情 code 已存在: {payload.code}")
        story = Story(
            id=new_id(EntityPrefix.STORY),
            project_id=project_id,
            code=payload.code,
            name=payload.name,
            layer=payload.layer.value,
            description=payload.description,
        )
        await self._stories.add(story)
        await self._bump(project_id)
        return self._to_read(await self._require_story(project_id, story.id))

    async def get(self, project_id: str, story_id: str) -> StoryRead:
        """获取剧情与图校验。"""
        return self._to_read(await self._require_story(project_id, story_id))

    async def list_stories(self, project_id: str) -> list[StorySummary]:
        """列出剧情。"""
        await self._require_project(project_id)
        return [self._to_summary(item) for item in await self._stories.list_by_project(project_id)]

    async def update(self, project_id: str, story_id: str, payload: StoryWrite) -> StoryRead:
        """更新剧情元数据。"""
        story = await self._require_story(project_id, story_id)
        self._assert_narrative_layer(payload.layer)
        duplicate = await self._stories.get_by_code(project_id, payload.code)
        if duplicate is not None and duplicate.id != story.id:
            raise ConflictError(f"剧情 code 已存在: {payload.code}")
        story.code = payload.code
        story.name = payload.name
        story.layer = payload.layer.value
        story.description = payload.description
        await self._bump(project_id)
        return self._to_read(await self._require_story(project_id, story.id))

    async def delete(self, project_id: str, story_id: str) -> None:
        """删除剧情。"""
        story = await self._require_story(project_id, story_id)
        await self._stories.delete(story)
        await self._bump(project_id)

    async def add_chapter(self, project_id: str, story_id: str, payload: StoryChapterWrite) -> StoryChapterRead:
        """新增章节。"""
        story = await self._require_story(project_id, story_id)
        if await self._stories.get_chapter_by_code(story.id, payload.code) is not None:
            raise ConflictError(f"章节 code 已存在: {payload.code}")
        saved = await self._stories.add_chapter(
            StoryChapter(
                id=new_id(EntityPrefix.STORY_CHAPTER),
                story_id=story.id,
                code=payload.code,
                name=payload.name,
                sort_order=payload.sort_order,
                summary=payload.summary,
            )
        )
        await self._bump(project_id)
        return self._to_chapter_read(saved)

    async def delete_chapter(self, project_id: str, story_id: str, chapter_id: str) -> None:
        """删除章节。"""
        await self._require_story(project_id, story_id)
        chapter = await self._stories.get_chapter(story_id, chapter_id)
        if chapter is None:
            raise NotFoundError("章节不存在")
        await self._stories.delete_chapter(chapter)
        await self._bump(project_id)

    async def update_chapter(
        self,
        project_id: str,
        story_id: str,
        chapter_id: str,
        payload: StoryChapterWrite,
    ) -> StoryChapterRead:
        """更新章节。"""
        story = await self._require_story(project_id, story_id)
        chapter = await self._stories.get_chapter(story_id, chapter_id)
        if chapter is None:
            raise NotFoundError("章节不存在")
        if payload.code != chapter.code:
            exists = await self._stories.get_chapter_by_code(story.id, payload.code)
            if exists is not None:
                raise ConflictError(f"章节 code 已存在: {payload.code}")
        chapter.code = payload.code
        chapter.name = payload.name
        chapter.sort_order = payload.sort_order
        chapter.summary = payload.summary
        await self._bump(project_id)
        return self._to_chapter_read(chapter)

    async def add_node(self, project_id: str, story_id: str, payload: StoryNodeWrite) -> StoryNodeRead:
        """新增节点。"""
        story = await self._require_story(project_id, story_id)
        if await self._stories.get_node_by_code(story.id, payload.code) is not None:
            raise ConflictError(f"节点 code 已存在: {payload.code}")
        await self._validate_node_payload(project_id, story, payload)
        if payload.is_entry:
            await self._stories.clear_entry_flags(story.id)
        node = StoryNode(id=new_id(EntityPrefix.STORY_NODE), story_id=story.id)
        self._apply_node(node, payload)
        await self._stories.add_node(node)
        await self._bump(project_id)
        loaded = await self._stories.get_node(story.id, node.id)
        assert loaded is not None
        return self._to_node_read(loaded)

    async def update_node(
        self, project_id: str, story_id: str, node_id: str, payload: StoryNodeWrite
    ) -> StoryNodeRead:
        """更新节点。"""
        story = await self._require_story(project_id, story_id)
        node = await self._require_node(story.id, node_id)
        duplicate = await self._stories.get_node_by_code(story.id, payload.code)
        if duplicate is not None and duplicate.id != node.id:
            raise ConflictError(f"节点 code 已存在: {payload.code}")
        await self._validate_node_payload(project_id, story, payload)
        if payload.is_entry:
            await self._stories.clear_entry_flags(story.id, keep_node_id=node.id)
        self._apply_node(node, payload)
        await self._bump(project_id)
        loaded = await self._stories.get_node(story.id, node.id)
        assert loaded is not None
        return self._to_node_read(loaded)

    async def delete_node(self, project_id: str, story_id: str, node_id: str) -> None:
        """删除节点。"""
        await self._require_story(project_id, story_id)
        node = await self._require_node(story_id, node_id)
        await self._stories.delete_node(node)
        await self._bump(project_id)

    async def add_edge(
        self, project_id: str, story_id: str, node_id: str, payload: StoryEdgeWrite
    ) -> StoryEdgeRead:
        """从节点连出一条边，立即检测无条件环。"""
        story = await self._require_story(project_id, story_id)
        from_node = await self._require_node(story.id, node_id)
        to_id = require_id(payload.to_node_id, EntityPrefix.STORY_NODE, field="to_node_id")
        to_node = await self._require_node(story.id, to_id)
        if await self._stories.get_edge_pair(from_node.id, to_node.id) is not None:
            raise ConflictError("这两节点之间已有连线")
        validate_conditional_terminator(
            is_conditional=payload.is_conditional,
            condition_note=payload.condition_note,
        )
        self._assert_new_edge(story, from_node.id, to_node.id, payload.is_conditional, payload.condition_note)
        saved = await self._stories.add_edge(
            StoryEdge(
                id=new_id(EntityPrefix.STORY_EDGE),
                from_node_id=from_node.id,
                to_node_id=to_node.id,
                is_conditional=payload.is_conditional,
                condition_note=payload.condition_note,
                sort_order=payload.sort_order,
            )
        )
        await self._bump(project_id)
        return self._to_edge_read(saved)

    async def delete_edge(self, project_id: str, story_id: str, node_id: str, edge_id: str) -> None:
        """删除边。若绑定选项则一并删除。"""
        await self._require_story(project_id, story_id)
        await self._require_node(story_id, node_id)
        edge = await self._stories.get_edge(node_id, edge_id)
        if edge is None:
            raise NotFoundError("剧情边不存在")
        if edge.choice_id is not None:
            choice = await self._stories.get_choice(node_id, edge.choice_id)
            if choice is not None:
                await self._stories.delete_choice(choice)
        await self._stories.delete_edge(edge)
        await self._bump(project_id)

    async def add_choice(
        self, project_id: str, story_id: str, node_id: str, payload: StoryChoiceWrite
    ) -> StoryChoiceRead:
        """为选项节点增加分支，同时建边。"""
        story = await self._require_story(project_id, story_id)
        node = await self._require_node(story.id, node_id)
        if node.node_type != StoryNodeType.CHOICE.value:
            raise ValidationError("只有 choice 节点可以添加选项", field="node_id")
        to_id = require_id(payload.to_node_id, EntityPrefix.STORY_NODE, field="to_node_id")
        to_node = await self._require_node(story.id, to_id)
        if await self._stories.get_edge_pair(node.id, to_node.id) is not None:
            raise ConflictError("这两节点之间已有连线")
        validate_conditional_terminator(
            is_conditional=payload.is_conditional,
            condition_note=payload.condition_note,
        )
        self._assert_new_edge(story, node.id, to_node.id, payload.is_conditional, payload.condition_note)
        choice = await self._stories.add_choice(
            StoryChoice(
                id=new_id(EntityPrefix.STORY_CHOICE),
                node_id=node.id,
                label=payload.label,
                sort_order=payload.sort_order,
            )
        )
        await self._stories.add_edge(
            StoryEdge(
                id=new_id(EntityPrefix.STORY_EDGE),
                from_node_id=node.id,
                to_node_id=to_node.id,
                choice_id=choice.id,
                is_conditional=payload.is_conditional,
                condition_note=payload.condition_note,
                sort_order=payload.sort_order,
            )
        )
        await self._bump(project_id)
        return StoryChoiceRead(
            id=choice.id,
            label=choice.label,
            to_node_id=to_node.id,
            sort_order=choice.sort_order,
        )

    async def delete_choice(self, project_id: str, story_id: str, node_id: str, choice_id: str) -> None:
        """删除选项及其边。"""
        await self._require_story(project_id, story_id)
        node = await self._require_node(story_id, node_id)
        choice = await self._stories.get_choice(node_id, choice_id)
        if choice is None:
            raise NotFoundError("选项不存在")
        for edge in node.outgoing:
            if edge.choice_id == choice.id:
                await self._stories.delete_edge(edge)
                break
        await self._stories.delete_choice(choice)
        await self._bump(project_id)

    async def add_condition(
        self, project_id: str, story_id: str, node_id: str, payload: StoryConditionWrite
    ) -> StoryConditionRead:
        """添加条件数据。"""
        await self._require_story(project_id, story_id)
        await self._require_node(story_id, node_id)
        saved = await self._stories.add_condition(
            StoryCondition(
                id=new_id(EntityPrefix.STORY_CONDITION),
                node_id=node_id,
                condition_type=payload.condition_type.value,
                expression=payload.expression,
                note=payload.note,
            )
        )
        await self._bump(project_id)
        return self._to_condition_read(saved)

    async def delete_condition(self, project_id: str, story_id: str, node_id: str, condition_id: str) -> None:
        """删除条件。"""
        await self._require_story(project_id, story_id)
        await self._require_node(story_id, node_id)
        item = await self._stories.get_condition(node_id, condition_id)
        if item is None:
            raise NotFoundError("剧情条件不存在")
        await self._stories.delete_condition(item)
        await self._bump(project_id)

    async def add_action(
        self, project_id: str, story_id: str, node_id: str, payload: StoryActionWrite
    ) -> StoryActionRead:
        """添加动作数据。"""
        await self._require_story(project_id, story_id)
        await self._require_node(story_id, node_id)
        saved = await self._stories.add_action(
            StoryAction(
                id=new_id(EntityPrefix.STORY_ACTION),
                node_id=node_id,
                action_type=payload.action_type.value,
                expression=payload.expression,
                note=payload.note,
            )
        )
        await self._bump(project_id)
        return self._to_action_read(saved)

    async def delete_action(self, project_id: str, story_id: str, node_id: str, action_id: str) -> None:
        """删除动作。"""
        await self._require_story(project_id, story_id)
        await self._require_node(story_id, node_id)
        item = await self._stories.get_action(node_id, action_id)
        if item is None:
            raise NotFoundError("剧情动作不存在")
        await self._stories.delete_action(item)
        await self._bump(project_id)

    async def add_cast(
        self, project_id: str, story_id: str, node_id: str, payload: StoryCastWrite
    ) -> StoryCastRead:
        """节点出场人物。不改写人物史实栏。"""
        await self._require_story(project_id, story_id)
        await self._require_node(story_id, node_id)
        character_id = require_id(payload.character_id, EntityPrefix.CHARACTER, field="character_id")
        character = await self._characters.get(project_id, character_id)
        if character is None:
            raise NotFoundError("人物不存在")
        if await self._stories.get_cast_by_character(node_id, character.id) is not None:
            raise ConflictError("该人物已出现在此节点")
        saved = await self._stories.add_cast(
            StoryNodeCharacter(
                id=new_id(EntityPrefix.STORY_NODE_CHARACTER),
                node_id=node_id,
                character_id=character.id,
                role=payload.role.value,
                note=payload.note,
            )
        )
        await self._bump(project_id)
        return self._to_cast_read(saved)

    async def delete_cast(self, project_id: str, story_id: str, node_id: str, cast_id: str) -> None:
        """移除出场人物。"""
        await self._require_story(project_id, story_id)
        await self._require_node(story_id, node_id)
        item = await self._stories.get_cast(node_id, cast_id)
        if item is None:
            raise NotFoundError("节点出场记录不存在")
        await self._stories.delete_cast(item)
        await self._bump(project_id)

    def _assert_narrative_layer(self, layer: BoundLayer) -> None:
        if layer == BoundLayer.HISTORICAL:
            raise ValidationError("剧情属于叙事层，不能标记为 historical", field="layer")

    def _apply_node(self, node: StoryNode, payload: StoryNodeWrite) -> None:
        node.code = payload.code
        node.name = payload.name
        node.node_type = payload.node_type.value
        node.chapter_id = payload.chapter_id
        node.is_entry = payload.is_entry
        node.is_ending = payload.is_ending
        node.sort_order = payload.sort_order
        node.title = payload.title
        node.body = payload.body
        node.event_id = payload.event_id
        node.character_id = payload.character_id
        node.city_id = payload.city_id
        node.faction_id = payload.faction_id

    async def _validate_node_payload(self, project_id: str, story: Story, payload: StoryNodeWrite) -> None:
        validate_node_reference(
            payload.node_type,
            event_id=payload.event_id,
            character_id=payload.character_id,
            city_id=payload.city_id,
            faction_id=payload.faction_id,
        )
        if payload.chapter_id is not None:
            chapter_id = require_id(payload.chapter_id, EntityPrefix.STORY_CHAPTER, field="chapter_id")
            if await self._stories.get_chapter(story.id, chapter_id) is None:
                raise NotFoundError("章节不存在")
        if payload.event_id is not None:
            event_id = require_id(payload.event_id, EntityPrefix.EVENT, field="event_id")
            if await self._events.get(project_id, event_id) is None:
                raise NotFoundError("事件不存在")
        if payload.character_id is not None:
            character_id = require_id(payload.character_id, EntityPrefix.CHARACTER, field="character_id")
            if await self._characters.get(project_id, character_id) is None:
                raise NotFoundError("人物不存在")
        if payload.city_id is not None:
            city_id = require_id(payload.city_id, EntityPrefix.CITY, field="city_id")
            if await self._cities.get(project_id, city_id) is None:
                raise NotFoundError("城池不存在")
        if payload.faction_id is not None:
            faction_id = require_id(payload.faction_id, EntityPrefix.FACTION, field="faction_id")
            if await self._factions.get(project_id, faction_id) is None:
                raise NotFoundError("势力不存在")

    def _assert_new_edge(
        self,
        story: Story,
        from_id: str,
        to_id: str,
        is_conditional: bool,
        condition_note: str | None,
    ) -> None:
        nodes, edges = self._graph_parts(story)
        node_ids = {item.id for item in nodes}
        new_edge = GraphEdge(
            from_id=from_id,
            to_id=to_id,
            is_conditional=is_conditional,
            has_terminator=bool(condition_note and condition_note.strip()),
        )
        assert_edge_allowed(node_ids, edges, new_edge)

    def _graph_parts(self, story: Story) -> tuple[list[GraphNode], list[GraphEdge]]:
        nodes = [
            GraphNode(id=node.id, is_entry=node.is_entry, is_ending=node.is_ending) for node in story.nodes
        ]
        edges: list[GraphEdge] = []
        for node in story.nodes:
            for edge in node.outgoing:
                edges.append(
                    GraphEdge(
                        from_id=edge.from_node_id,
                        to_id=edge.to_node_id,
                        is_conditional=edge.is_conditional,
                        has_terminator=bool(edge.condition_note and edge.condition_note.strip()),
                    )
                )
        return nodes, edges

    def _to_graph(self, story: Story) -> StoryGraphRead:
        nodes, edges = self._graph_parts(story)
        report = analyze_story_graph(nodes, edges)
        return StoryGraphRead(
            valid=report.valid,
            errors=list(report.errors),
            has_unconditional_cycle=report.has_unconditional_cycle,
            entry_reaches_ending=report.entry_reaches_ending,
            entry_count=report.entry_count,
            ending_count=report.ending_count,
            node_count=len(story.nodes),
            edge_count=len(edges),
        )

    def _to_read(self, story: Story) -> StoryRead:
        chapters = sorted(story.chapters, key=lambda item: (item.sort_order, item.code))
        nodes = sorted(story.nodes, key=lambda item: (item.sort_order, item.code))
        return StoryRead(
            id=story.id,
            project_id=story.project_id,
            code=story.code,
            name=story.name,
            layer=BoundLayer(story.layer),
            description=story.description,
            chapters=[self._to_chapter_read(item) for item in chapters],
            nodes=[self._to_node_read(item) for item in nodes],
            graph=self._to_graph(story),
        )

    def _to_summary(self, story: Story) -> StorySummary:
        graph = self._to_graph(story)
        return StorySummary(
            id=story.id,
            project_id=story.project_id,
            code=story.code,
            name=story.name,
            layer=BoundLayer(story.layer),
            node_count=len(story.nodes),
            chapter_count=len(story.chapters),
            graph_valid=graph.valid,
        )

    def _to_chapter_read(self, chapter: StoryChapter) -> StoryChapterRead:
        return StoryChapterRead(
            id=chapter.id,
            code=chapter.code,
            name=chapter.name,
            sort_order=chapter.sort_order,
            summary=chapter.summary,
        )

    def _to_node_read(self, node: StoryNode) -> StoryNodeRead:
        choice_targets = {edge.choice_id: edge.to_node_id for edge in node.outgoing if edge.choice_id}
        return StoryNodeRead(
            id=node.id,
            chapter_id=node.chapter_id,
            code=node.code,
            name=node.name,
            node_type=StoryNodeType(node.node_type),
            is_entry=node.is_entry,
            is_ending=node.is_ending,
            sort_order=node.sort_order,
            title=node.title,
            body=node.body,
            event=self._event_ref(node.event),
            character=self._character_ref(node.character),
            city=self._city_ref(node.city),
            faction=self._faction_ref(node.faction),
            outgoing=[self._to_edge_read(item) for item in node.outgoing],
            choices=[
                StoryChoiceRead(
                    id=item.id,
                    label=item.label,
                    to_node_id=choice_targets.get(item.id),
                    sort_order=item.sort_order,
                )
                for item in node.choices
            ],
            conditions=[self._to_condition_read(item) for item in node.conditions],
            actions=[self._to_action_read(item) for item in node.actions],
            cast=[self._to_cast_read(item) for item in node.cast],
        )

    def _to_edge_read(self, edge: StoryEdge) -> StoryEdgeRead:
        return StoryEdgeRead(
            id=edge.id,
            from_node_id=edge.from_node_id,
            to_node_id=edge.to_node_id,
            choice_id=edge.choice_id,
            is_conditional=edge.is_conditional,
            condition_note=edge.condition_note,
            sort_order=edge.sort_order,
        )

    def _to_condition_read(self, item: StoryCondition) -> StoryConditionRead:
        return StoryConditionRead(
            id=item.id,
            condition_type=StoryConditionType(item.condition_type),
            expression=item.expression,
            note=item.note,
        )

    def _to_action_read(self, item: StoryAction) -> StoryActionRead:
        return StoryActionRead(
            id=item.id,
            action_type=StoryActionType(item.action_type),
            expression=item.expression,
            note=item.note,
        )

    def _to_cast_read(self, item: StoryNodeCharacter) -> StoryCastRead:
        character = item.character
        return StoryCastRead(
            id=item.id,
            character=CharacterRef(id=character.id, code=character.code, name=character.name),
            role=StoryCastRole(item.role),
            note=item.note,
        )

    def _event_ref(self, event) -> EventRef | None:
        if event is None:
            return None
        return EventRef(id=event.id, code=event.code, name=event.name, year=event.year)

    def _character_ref(self, character) -> CharacterRef | None:
        if character is None:
            return None
        return CharacterRef(id=character.id, code=character.code, name=character.name)

    def _city_ref(self, city) -> CityRef | None:
        if city is None:
            return None
        return CityRef(id=city.id, code=city.code, name=city.name)

    def _faction_ref(self, faction) -> FactionRef | None:
        if faction is None:
            return None
        return FactionRef(id=faction.id, code=faction.code, name=faction.name, color=faction.color)

    async def _require_story(self, project_id: str, story_id: str) -> Story:
        story = await self._stories.get(project_id, story_id)
        if story is None:
            raise NotFoundError("剧情不存在")
        return story

    async def _require_node(self, story_id: str, node_id: str) -> StoryNode:
        node = await self._stories.get_node(story_id, node_id)
        if node is None:
            raise NotFoundError("剧情节点不存在")
        return node

    async def _require_project(self, project_id: str):
        project = await self._projects.get(project_id)
        if project is None:
            raise NotFoundError("项目不存在")
        return project

    async def _bump(self, project_id: str) -> None:
        project = await self._projects.get(project_id)
        if project is not None:
            await self._projects.bump_content_version(project)
