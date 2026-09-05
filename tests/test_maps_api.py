"""Phase 7 地图测试。地形稀疏存储，城池挂坐标，不做 Canvas。"""

import pytest
from httpx import AsyncClient

from backend.core.exceptions import ValidationError
from backend.domain.map_rules import MapFeatureType, validate_cell_in_bounds, validate_feature_points
from tests.test_characters_api import _create_project
from tests.test_cities_factions_api import CHENGDU


def test_cell_outside_map_is_invalid() -> None:
    with pytest.raises(ValidationError):
        validate_cell_in_bounds(20, 0, width=20, height=16)


def test_mountain_needs_three_points() -> None:
    with pytest.raises(ValidationError):
        validate_feature_points(MapFeatureType.MOUNTAIN, [(0.0, 0.0), (1.0, 1.0)], width=20, height=16)


@pytest.mark.asyncio
async def test_create_map_patch_terrain_and_place_city(client: AsyncClient) -> None:
    project_id = await _create_project(client)
    created = await client.post(
        f"/api/v1/projects/{project_id}/maps",
        json={"code": "han_land", "name": "汉末九州", "width": 20, "height": 16, "description": "编辑器数据，不渲染。"},
    )
    assert created.status_code == 201
    game_map = created.json()["data"]
    assert game_map["id"].startswith("map_")
    assert game_map["terrain_cell_count"] == 0
    assert game_map["features"] == []
    map_id = game_map["id"]

    patched = await client.patch(
        f"/api/v1/projects/{project_id}/maps/{map_id}/terrain",
        json={
            "cells": [
                {"x": 3, "y": 4, "terrain": "water"},
                {"x": 4, "y": 4, "terrain": "forest"},
            ]
        },
    )
    assert patched.status_code == 200
    assert patched.json()["meta"]["total"] == 2

    river = await client.post(
        f"/api/v1/projects/{project_id}/maps/{map_id}/features",
        json={
            "code": "yangtze",
            "name": "长江",
            "feature_type": "river",
            "points": [{"x": 0, "y": 8}, {"x": 10, "y": 9}, {"x": 19, "y": 8}],
        },
    )
    assert river.status_code == 201
    assert river.json()["data"]["id"].startswith("mft_")

    city = await client.post(f"/api/v1/projects/{project_id}/cities", json=CHENGDU)
    city_id = city.json()["data"]["id"]
    placed = await client.post(
        f"/api/v1/projects/{project_id}/maps/{map_id}/cities",
        json={"city_id": city_id, "coord_x": 5, "coord_y": 7},
    )
    assert placed.status_code == 201
    detail = await client.get(f"/api/v1/projects/{project_id}/maps/{map_id}")
    body = detail.json()["data"]
    assert body["terrain_cell_count"] == 2
    assert body["cities"][0]["name"] == "成都"
    assert body["cities"][0]["coord_x"] == 5
    city_detail = await client.get(f"/api/v1/projects/{project_id}/cities/{city_id}")
    assert city_detail.json()["data"]["map_id"] == map_id


@pytest.mark.asyncio
async def test_reject_out_of_bounds_and_invalid_geometry(client: AsyncClient) -> None:
    project_id = await _create_project(client)
    created = await client.post(
        f"/api/v1/projects/{project_id}/maps",
        json={"code": "small_map", "name": "小图", "width": 8, "height": 8},
    )
    map_id = created.json()["data"]["id"]
    oob = await client.patch(
        f"/api/v1/projects/{project_id}/maps/{map_id}/terrain",
        json={"cells": [{"x": 8, "y": 0, "terrain": "water"}]},
    )
    assert oob.status_code == 400

    unknown = await client.patch(
        f"/api/v1/projects/{project_id}/maps/{map_id}/terrain",
        json={"cells": [{"x": 0, "y": 0, "terrain": "lava"}]},
    )
    assert unknown.status_code == 422

    mountain = await client.post(
        f"/api/v1/projects/{project_id}/maps/{map_id}/features",
        json={
            "code": "qinling",
            "name": "秦岭",
            "feature_type": "mountain",
            "points": [{"x": 1, "y": 1}, {"x": 2, "y": 2}],
        },
    )
    assert mountain.status_code == 400


@pytest.mark.asyncio
async def test_two_cities_cannot_share_a_cell_and_delete_unbinds(client: AsyncClient) -> None:
    project_id = await _create_project(client)
    created = await client.post(
        f"/api/v1/projects/{project_id}/maps",
        json={"code": "yi_map", "name": "益州图", "width": 12, "height": 12},
    )
    map_id = created.json()["data"]["id"]
    first = await client.post(f"/api/v1/projects/{project_id}/cities", json=CHENGDU)
    second = await client.post(
        f"/api/v1/projects/{project_id}/cities",
        json={"code": "hanzhong", "name": "汉中", "historical": {"description": "汉中郡。"}},
    )
    first_id = first.json()["data"]["id"]
    second_id = second.json()["data"]["id"]
    ok = await client.post(
        f"/api/v1/projects/{project_id}/maps/{map_id}/cities",
        json={"city_id": first_id, "coord_x": 3, "coord_y": 3},
    )
    assert ok.status_code == 201
    conflict = await client.post(
        f"/api/v1/projects/{project_id}/maps/{map_id}/cities",
        json={"city_id": second_id, "coord_x": 3, "coord_y": 3},
    )
    assert conflict.status_code == 409

    deleted = await client.delete(f"/api/v1/projects/{project_id}/maps/{map_id}")
    assert deleted.status_code == 200
    city = await client.get(f"/api/v1/projects/{project_id}/cities/{first_id}")
    assert city.json()["data"]["map_id"] is None
