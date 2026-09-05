"""冻结合同 API 与导出目录可被客户端加载器读取。"""

from pathlib import Path

import pytest
from httpx import AsyncClient

from game_data_loader import load_export_dir

LIU_BEI = {
    "base": {
        "code": "chr_liu_bei",
        "name": "刘备",
        "courtesy_name": "玄德",
        "gender": "male",
        "birth_year": 161,
        "death_year": 223,
    },
    "historical": {"biography": "蜀汉开国皇帝。"},
    "game": {"force": 72, "intelligence": 80, "charisma": 95},
}


@pytest.mark.asyncio
async def test_client_schema_endpoint(client: AsyncClient) -> None:
    response = await client.get("/api/v1/client-schema")
    assert response.status_code == 200
    body = response.json()["data"]
    assert body["schema_version"] == "1.12.0"
    assert body["loader"] == "game_data_loader"
    assert "characters.json" in body["files"]
    assert "quests.json" in body["unsupported_files"]
    assert "package.schema.json" in body["schema_documents"]


@pytest.mark.asyncio
async def test_exported_directory_loads_in_client_loader(client: AsyncClient) -> None:
    created = await client.post("/api/v1/projects", json={"name": "冻结验收"})
    project_id = created.json()["data"]["id"]
    await client.post(f"/api/v1/projects/{project_id}/characters", json=LIU_BEI)
    exported = await client.post(f"/api/v1/projects/{project_id}/export")
    assert exported.status_code == 200
    export_dir = Path(exported.json()["data"]["export_dir"])
    data = load_export_dir(export_dir)
    liu = data.character_by_code("chr_liu_bei")
    assert liu.name == "刘备"
    assert liu.force == 72
