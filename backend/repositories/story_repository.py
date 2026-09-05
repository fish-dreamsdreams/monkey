"""剧情仓储。"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

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


class StoryRepository:
    """剧情聚合持久化。"""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _detail_options(self) -> tuple[object, ...]:
        return (
            selectinload(Story.chapters),
            selectinload(Story.nodes).selectinload(StoryNode.event),
            selectinload(Story.nodes).selectinload(StoryNode.character),
            selectinload(Story.nodes).selectinload(StoryNode.city),
            selectinload(Story.nodes).selectinload(StoryNode.faction),
            selectinload(Story.nodes).selectinload(StoryNode.outgoing),
            selectinload(Story.nodes).selectinload(StoryNode.choices),
            selectinload(Story.nodes).selectinload(StoryNode.conditions),
            selectinload(Story.nodes).selectinload(StoryNode.actions),
            selectinload(Story.nodes).selectinload(StoryNode.cast).selectinload(StoryNodeCharacter.character),
        )

    async def add(self, story: Story) -> Story:
        """插入剧情。"""
        self._session.add(story)
        await self._session.flush()
        return story

    async def get(self, project_id: str, story_id: str) -> Story | None:
        """按 ID 加载剧情聚合。"""
        result = await self._session.execute(
            select(Story)
            .options(*self._detail_options())
            .where(Story.project_id == project_id, Story.id == story_id)
        )
        return result.scalar_one_or_none()

    async def get_by_code(self, project_id: str, code: str) -> Story | None:
        """按业务 code 加载剧情。"""
        result = await self._session.execute(
            select(Story).where(Story.project_id == project_id, Story.code == code)
        )
        return result.scalar_one_or_none()

    async def list_by_project(self, project_id: str) -> list[Story]:
        """列出项目剧情（含节点与边，供图校验）。"""
        result = await self._session.execute(
            select(Story)
            .options(
                selectinload(Story.chapters),
                selectinload(Story.nodes).selectinload(StoryNode.outgoing),
            )
            .where(Story.project_id == project_id)
            .order_by(Story.name, Story.code)
        )
        return list(result.scalars().all())

    async def delete(self, story: Story) -> None:
        """删除剧情。"""
        await self._session.delete(story)
        await self._session.flush()

    async def add_chapter(self, chapter: StoryChapter) -> StoryChapter:
        """插入章节。"""
        self._session.add(chapter)
        await self._session.flush()
        return chapter

    async def get_chapter(self, story_id: str, chapter_id: str) -> StoryChapter | None:
        """加载章节。"""
        result = await self._session.execute(
            select(StoryChapter).where(StoryChapter.story_id == story_id, StoryChapter.id == chapter_id)
        )
        return result.scalar_one_or_none()

    async def get_chapter_by_code(self, story_id: str, code: str) -> StoryChapter | None:
        """按 code 查找章节。"""
        result = await self._session.execute(
            select(StoryChapter).where(StoryChapter.story_id == story_id, StoryChapter.code == code)
        )
        return result.scalar_one_or_none()

    async def delete_chapter(self, chapter: StoryChapter) -> None:
        """删除章节。节点 chapter_id 置空。"""
        await self._session.delete(chapter)
        await self._session.flush()

    async def add_node(self, node: StoryNode) -> StoryNode:
        """插入节点。"""
        self._session.add(node)
        await self._session.flush()
        return node

    async def get_node(self, story_id: str, node_id: str) -> StoryNode | None:
        """加载节点。"""
        result = await self._session.execute(
            select(StoryNode)
            .options(
                selectinload(StoryNode.outgoing),
                selectinload(StoryNode.choices),
                selectinload(StoryNode.conditions),
                selectinload(StoryNode.actions),
                selectinload(StoryNode.cast).selectinload(StoryNodeCharacter.character),
                selectinload(StoryNode.event),
                selectinload(StoryNode.character),
                selectinload(StoryNode.city),
                selectinload(StoryNode.faction),
            )
            .where(StoryNode.story_id == story_id, StoryNode.id == node_id)
        )
        return result.scalar_one_or_none()

    async def get_node_by_code(self, story_id: str, code: str) -> StoryNode | None:
        """按 code 查找节点。"""
        result = await self._session.execute(
            select(StoryNode).where(StoryNode.story_id == story_id, StoryNode.code == code)
        )
        return result.scalar_one_or_none()

    async def list_nodes(self, story_id: str) -> list[StoryNode]:
        """列出剧情全部节点。"""
        result = await self._session.execute(
            select(StoryNode)
            .options(selectinload(StoryNode.outgoing))
            .where(StoryNode.story_id == story_id)
        )
        return list(result.scalars().all())

    async def delete_node(self, node: StoryNode) -> None:
        """删除节点。"""
        await self._session.delete(node)
        await self._session.flush()

    async def clear_entry_flags(self, story_id: str, keep_node_id: str | None = None) -> None:
        """保证至多一个入口。"""
        nodes = await self.list_nodes(story_id)
        for node in nodes:
            if keep_node_id is not None and node.id == keep_node_id:
                continue
            if node.is_entry:
                node.is_entry = False

    async def add_edge(self, edge: StoryEdge) -> StoryEdge:
        """插入边。"""
        self._session.add(edge)
        await self._session.flush()
        return edge

    async def get_edge(self, from_node_id: str, edge_id: str) -> StoryEdge | None:
        """加载边。"""
        result = await self._session.execute(
            select(StoryEdge).where(StoryEdge.from_node_id == from_node_id, StoryEdge.id == edge_id)
        )
        return result.scalar_one_or_none()

    async def get_edge_pair(self, from_node_id: str, to_node_id: str) -> StoryEdge | None:
        """按两端查找边。"""
        result = await self._session.execute(
            select(StoryEdge).where(
                StoryEdge.from_node_id == from_node_id,
                StoryEdge.to_node_id == to_node_id,
            )
        )
        return result.scalar_one_or_none()

    async def delete_edge(self, edge: StoryEdge) -> None:
        """删除边。"""
        await self._session.delete(edge)
        await self._session.flush()

    async def add_choice(self, choice: StoryChoice) -> StoryChoice:
        """插入选项。"""
        self._session.add(choice)
        await self._session.flush()
        return choice

    async def get_choice(self, node_id: str, choice_id: str) -> StoryChoice | None:
        """加载选项。"""
        result = await self._session.execute(
            select(StoryChoice).where(StoryChoice.node_id == node_id, StoryChoice.id == choice_id)
        )
        return result.scalar_one_or_none()

    async def delete_choice(self, choice: StoryChoice) -> None:
        """删除选项。"""
        await self._session.delete(choice)
        await self._session.flush()

    async def add_condition(self, item: StoryCondition) -> StoryCondition:
        """插入条件。"""
        self._session.add(item)
        await self._session.flush()
        return item

    async def get_condition(self, node_id: str, condition_id: str) -> StoryCondition | None:
        """加载条件。"""
        result = await self._session.execute(
            select(StoryCondition).where(
                StoryCondition.node_id == node_id,
                StoryCondition.id == condition_id,
            )
        )
        return result.scalar_one_or_none()

    async def delete_condition(self, item: StoryCondition) -> None:
        """删除条件。"""
        await self._session.delete(item)
        await self._session.flush()

    async def add_action(self, item: StoryAction) -> StoryAction:
        """插入动作。"""
        self._session.add(item)
        await self._session.flush()
        return item

    async def get_action(self, node_id: str, action_id: str) -> StoryAction | None:
        """加载动作。"""
        result = await self._session.execute(
            select(StoryAction).where(StoryAction.node_id == node_id, StoryAction.id == action_id)
        )
        return result.scalar_one_or_none()

    async def delete_action(self, item: StoryAction) -> None:
        """删除动作。"""
        await self._session.delete(item)
        await self._session.flush()

    async def add_cast(self, item: StoryNodeCharacter) -> StoryNodeCharacter:
        """插入出场人物。"""
        self._session.add(item)
        await self._session.flush()
        loaded = await self._session.execute(
            select(StoryNodeCharacter)
            .options(selectinload(StoryNodeCharacter.character))
            .where(StoryNodeCharacter.id == item.id)
        )
        return loaded.scalar_one()

    async def get_cast(self, node_id: str, cast_id: str) -> StoryNodeCharacter | None:
        """加载出场记录。"""
        result = await self._session.execute(
            select(StoryNodeCharacter).where(
                StoryNodeCharacter.node_id == node_id,
                StoryNodeCharacter.id == cast_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_cast_by_character(self, node_id: str, character_id: str) -> StoryNodeCharacter | None:
        """按人物查找出场。"""
        result = await self._session.execute(
            select(StoryNodeCharacter).where(
                StoryNodeCharacter.node_id == node_id,
                StoryNodeCharacter.character_id == character_id,
            )
        )
        return result.scalar_one_or_none()

    async def delete_cast(self, item: StoryNodeCharacter) -> None:
        """删除出场记录。"""
        await self._session.delete(item)
        await self._session.flush()
