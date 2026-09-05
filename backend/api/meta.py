"""编辑器元信息 API。"""

from fastapi import APIRouter

from backend.core.alembic_runtime import script_head_revision
from backend.core.ids import EntityPrefix
from backend.core.schema_version import API_VERSION, CURRENT_SCHEMA_VERSION, SUPPORTED_SCHEMA_VERSIONS
from backend.domain.relationship_types import (
    RELATIONSHIP_TYPE_LABELS_ZH,
    RelationshipType,
    is_symmetric,
)
from backend.domain.event_rules import (
    EVENT_FACTION_ROLE_LABELS_ZH,
    EVENT_PARTICIPANT_ROLE_LABELS_ZH,
    EVENT_TYPE_LABELS_ZH,
    EventFactionRole,
    EventParticipantRole,
    EventType,
)
from backend.domain.faction_rules import FACTION_MEMBER_ROLE_LABELS_ZH, FactionMemberRole
from backend.domain.map_rules import (
    MAP_FEATURE_TYPE_LABELS_ZH,
    TERRAIN_TYPE_LABELS_ZH,
    MapFeatureType,
    TerrainType,
)
from backend.domain.skill_rules import (
    EFFECT_TYPE_LABELS_ZH,
    SKILL_TYPE_LABELS_ZH,
    SkillEffectType,
    SkillType,
)
from backend.domain.source_types import SOURCE_TYPE_LABELS_ZH, SourceType, is_fact_eligible
from backend.schemas.common import ApiResponse
from backend.schemas.project import EditorMetaRead
from backend.schemas.faction import MemberRoleMeta
from backend.schemas.map import TypeMeta
from backend.schemas.relationship import RelationshipTypeMeta
from backend.schemas.skill import SkillTypeMeta
from backend.schemas.source import SourceTypeMeta

router = APIRouter(tags=["meta"])


@router.get("/meta")
async def get_editor_meta() -> ApiResponse[EditorMetaRead]:
    """返回当前编辑器 schema、ID 前缀与 Alembic 脚本 head。"""
    data = EditorMetaRead(
        api_version=API_VERSION,
        schema_version=CURRENT_SCHEMA_VERSION,
        supported_schema_versions=sorted(SUPPORTED_SCHEMA_VERSIONS),
        alembic_script_head=script_head_revision(),
        id_prefixes={item.name.lower(): item.value for item in EntityPrefix},
        source_types=[
            SourceTypeMeta(
                code=item.value,
                name_zh=SOURCE_TYPE_LABELS_ZH[item],
                fact_eligible=is_fact_eligible(item),
            )
            for item in SourceType
        ],
        relationship_types=[
            RelationshipTypeMeta(
                code=item.value,
                name_zh=RELATIONSHIP_TYPE_LABELS_ZH[item],
                symmetric=is_symmetric(item),
            )
            for item in RelationshipType
        ],
        skill_types=[
            SkillTypeMeta(code=item.value, name_zh=SKILL_TYPE_LABELS_ZH[item]) for item in SkillType
        ],
        effect_types=[
            SkillTypeMeta(code=item.value, name_zh=EFFECT_TYPE_LABELS_ZH[item]) for item in SkillEffectType
        ],
        member_roles=[
            MemberRoleMeta(code=item.value, name_zh=FACTION_MEMBER_ROLE_LABELS_ZH[item])
            for item in FactionMemberRole
        ],
        terrain_types=[
            TypeMeta(code=item.value, name_zh=TERRAIN_TYPE_LABELS_ZH[item]) for item in TerrainType
        ],
        map_feature_types=[
            TypeMeta(code=item.value, name_zh=MAP_FEATURE_TYPE_LABELS_ZH[item]) for item in MapFeatureType
        ],
        event_types=[TypeMeta(code=item.value, name_zh=EVENT_TYPE_LABELS_ZH[item]) for item in EventType],
        participant_roles=[
            TypeMeta(code=item.value, name_zh=EVENT_PARTICIPANT_ROLE_LABELS_ZH[item])
            for item in EventParticipantRole
        ],
        event_faction_roles=[
            TypeMeta(code=item.value, name_zh=EVENT_FACTION_ROLE_LABELS_ZH[item]) for item in EventFactionRole
        ],
    )
    return ApiResponse(data=data)
