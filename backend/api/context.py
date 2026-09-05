"""项目上下文依赖。

职责：所有内容 API 进入业务前，先校验项目 ID 格式、项目存在性和 schema 兼容性。
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.db import get_db
from backend.core.exceptions import NotFoundError, UnsupportedSchemaError
from backend.core.ids import EntityPrefix, require_id
from backend.core.schema_version import SUPPORTED_SCHEMA_VERSIONS
from backend.models.project import Project
from backend.repositories.project_repository import ProjectRepository


class ProjectContext:
    """当前请求对应的内容项目。"""

    def __init__(self, project: Project) -> None:
        self.project = project
        self.id = project.id
        self.code = project.code
        self.schema_version = project.schema_version


def valid_project_id(project_id: str) -> str:
    """校验路径参数 project_id。"""
    return require_id(project_id, EntityPrefix.PROJECT, field="project_id")


def valid_character_id(character_id: str) -> str:
    """校验路径参数 character_id。"""
    return require_id(character_id, EntityPrefix.CHARACTER, field="character_id")


def valid_citation_id(citation_id: str) -> str:
    """校验路径参数 citation_id。"""
    return require_id(citation_id, EntityPrefix.CITATION, field="citation_id")


def valid_personality_tag_id(tag_id: str) -> str:
    """校验路径参数 tag_id。"""
    return require_id(tag_id, EntityPrefix.PERSONALITY_TAG, field="tag_id")


def valid_source_id(source_id: str) -> str:
    """校验路径参数 source_id。"""
    return require_id(source_id, EntityPrefix.SOURCE, field="source_id")


def valid_relationship_id(relationship_id: str) -> str:
    """校验路径参数 relationship_id。"""
    return require_id(relationship_id, EntityPrefix.RELATIONSHIP, field="relationship_id")


def valid_skill_id(skill_id: str) -> str:
    """校验路径参数 skill_id。"""
    return require_id(skill_id, EntityPrefix.SKILL, field="skill_id")


def valid_character_skill_id(binding_id: str) -> str:
    """校验路径参数 binding_id（人物技能绑定）。"""
    return require_id(binding_id, EntityPrefix.CHARACTER_SKILL, field="binding_id")


def valid_city_id(city_id: str) -> str:
    """校验路径参数 city_id。"""
    return require_id(city_id, EntityPrefix.CITY, field="city_id")


def valid_faction_id(faction_id: str) -> str:
    """校验路径参数 faction_id。"""
    return require_id(faction_id, EntityPrefix.FACTION, field="faction_id")


def valid_faction_member_id(member_id: str) -> str:
    """校验路径参数 member_id。"""
    return require_id(member_id, EntityPrefix.FACTION_MEMBER, field="member_id")


def valid_faction_territory_id(territory_id: str) -> str:
    """校验路径参数 territory_id。"""
    return require_id(territory_id, EntityPrefix.FACTION_TERRITORY, field="territory_id")


def valid_map_id(map_id: str) -> str:
    """校验路径参数 map_id。"""
    return require_id(map_id, EntityPrefix.MAP, field="map_id")


def valid_map_feature_id(feature_id: str) -> str:
    """校验路径参数 feature_id。"""
    return require_id(feature_id, EntityPrefix.MAP_FEATURE, field="feature_id")


def valid_event_id(event_id: str) -> str:
    """校验路径参数 event_id。"""
    return require_id(event_id, EntityPrefix.EVENT, field="event_id")


def valid_event_participant_id(participant_id: str) -> str:
    """校验路径参数 participant_id。"""
    return require_id(participant_id, EntityPrefix.EVENT_PARTICIPANT, field="participant_id")


def valid_event_faction_id(link_id: str) -> str:
    """校验路径参数 link_id。"""
    return require_id(link_id, EntityPrefix.EVENT_FACTION, field="link_id")


def valid_event_source_id(citation_id: str) -> str:
    """校验路径参数 citation_id。"""
    return require_id(citation_id, EntityPrefix.EVENT_SOURCE, field="citation_id")


def valid_story_id(story_id: str) -> str:
    """校验路径参数 story_id。"""
    return require_id(story_id, EntityPrefix.STORY, field="story_id")


def valid_story_chapter_id(chapter_id: str) -> str:
    """校验路径参数 chapter_id。"""
    return require_id(chapter_id, EntityPrefix.STORY_CHAPTER, field="chapter_id")


def valid_story_node_id(node_id: str) -> str:
    """校验路径参数 node_id。"""
    return require_id(node_id, EntityPrefix.STORY_NODE, field="node_id")


def valid_story_edge_id(edge_id: str) -> str:
    """校验路径参数 edge_id。"""
    return require_id(edge_id, EntityPrefix.STORY_EDGE, field="edge_id")


def valid_story_choice_id(choice_id: str) -> str:
    """校验路径参数 choice_id。"""
    return require_id(choice_id, EntityPrefix.STORY_CHOICE, field="choice_id")


def valid_story_condition_id(condition_id: str) -> str:
    """校验路径参数 condition_id。"""
    return require_id(condition_id, EntityPrefix.STORY_CONDITION, field="condition_id")


def valid_story_action_id(action_id: str) -> str:
    """校验路径参数 action_id。"""
    return require_id(action_id, EntityPrefix.STORY_ACTION, field="action_id")


def valid_story_cast_id(cast_id: str) -> str:
    """校验路径参数 cast_id。"""
    return require_id(cast_id, EntityPrefix.STORY_NODE_CHARACTER, field="cast_id")


def valid_resource_id(resource_id: str) -> str:
    """校验路径参数 resource_id。"""
    return require_id(resource_id, EntityPrefix.RESOURCE, field="resource_id")


async def get_project_context(
    project_id: str = Depends(valid_project_id),
    session: AsyncSession = Depends(get_db),
) -> ProjectContext:
    """加载并校验当前项目上下文。"""
    project = await ProjectRepository(session).get(project_id)
    if project is None:
        raise NotFoundError("项目不存在")
    if project.schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        raise UnsupportedSchemaError(
            f"项目 schema_version={project.schema_version} 不被当前编辑器支持"
        )
    return ProjectContext(project)
