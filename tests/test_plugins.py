import importlib
from collections.abc import Callable
from typing import Any, Literal, Optional, Union, get_args, get_origin

import pytest
from pydantic import BaseModel, ConfigDict, Field


class MatchMataConfig(BaseModel):
    disable_duplicate_school_detect: bool = Field(False, alias="disableDuplicateSchoolDetect")
    enable_talent_find: bool = Field(False, alias="enableTalentFind")
    use_fast: bool = Field(True, alias="useFast")
    max_team_member: int = Field(2, alias="maxTeamMember")
    cache: dict[str, str] = Field({})
    disable_cache: bool = Field(True, alias="disableCache")
    enable_random_sort_team: bool = Field(False, alias="enableRandomSortTeam")
    user_star_display: bool = Field(True, alias="userStarDisplay")
    ignore_teacher_score: bool = Field(False, alias="ignoreTeacherScore")
    algorithm_version: Literal["v3", "anchor"] = Field("anchor", alias="algorithmVersion")
    advanced_match: bool = Field(False, alias="advancedMatch")
    is_search_all: bool = Field(False, alias="isSearchAll")
    enable_matching_for_enterprise: bool = Field(False, alias="enableMatchingForEnterprise")

    model_config = ConfigDict(populate_by_name=True)


def resolve_base_type(annotation: Any) -> Any:
    origin = get_origin(annotation)
    if origin is Union:
        args = get_args(annotation)
        for arg in args:
            if arg is not type(None):
                return resolve_base_type(arg)
    if origin is Literal:
        return str
    return origin or annotation


def get_alias_set(fields: dict[str, Any]) -> set[str]:
    return {field.alias or name for name, field in fields.items()}


def get_alias_type_map(fields: dict[str, Any]) -> dict[str, type]:
    return {(field.alias or name): resolve_base_type(field.annotation) for name, field in fields.items()}


def test_resolve_annotation():
    builder = importlib.import_module("framex.plugins.proxy.builder")
    resolve_annotation: Callable = getattr(builder, "resolve_annotation")
    reset_created_models: Callable = getattr(builder, "reset_created_models")

    reset_created_models()

    # Test BaseType gen
    assert resolve_annotation({"type": "string", "title": "Task"}, {}) is str
    assert (
        resolve_annotation({"items": {"type": "string"}, "type": "array", "title": "Sub Tasks", "default": []}, {})
        == list[str]
    )
    assert (
        resolve_annotation({"items": {"type": "number"}, "type": "array", "title": "Weights", "default": []}, {})
        == list[float]
    )

    # Test BaseModel gen
    prop_schema = {"$ref": "#/components/schemas/MatchMataConfig"}
    components = {
        "MatchMataConfig": {
            "properties": {
                "disableDuplicateSchoolDetect": {
                    "type": "boolean",
                    "title": "Disableduplicateschooldetect",
                    "default": False,
                },
                "enableTalentFind": {"type": "boolean", "title": "Enabletalentfind", "default": False},
                "useFast": {"type": "boolean", "title": "Usefast", "default": True},
                "maxTeamMember": {"type": "integer", "title": "Maxteammember", "default": 2},
                "cache": {
                    "additionalProperties": {"type": "string"},
                    "type": "object",
                    "title": "Cache",
                    "default": {},
                },
                "disableCache": {"type": "boolean", "title": "Disablecache", "default": True},
                "enableRandomSortTeam": {"type": "boolean", "title": "Enablerandomsortteam", "default": False},
                "userStarDisplay": {"type": "boolean", "title": "Userstardisplay", "default": True},
                "ignoreTeacherScore": {"type": "boolean", "title": "Ignoreteacherscore", "default": False},
                "algorithmVersion": {
                    "type": "string",
                    "enum": ["v3", "anchor"],
                    "title": "Algorithmversion",
                    "default": "anchor",
                },
                "advancedMatch": {"type": "boolean", "title": "Advancedmatch", "default": False},
                "isSearchAll": {"type": "boolean", "title": "Issearchall", "default": False},
                "enableMatchingForEnterprise": {
                    "type": "boolean",
                    "title": "Enablematchingforenterprise",
                    "default": False,
                },
            },
            "type": "object",
            "title": "MatchMataConfig",
        }
    }
    f1 = resolve_annotation(prop_schema, components).model_fields
    f2 = MatchMataConfig.model_fields

    assert get_alias_type_map(f1) == get_alias_type_map(f2), "Alias sets do not match"

    # Test Exception
    with pytest.raises(RuntimeError) as exc_info:
        resolve_annotation({"$ref": "#/components/schemas/MatchMataConfig"}, {})

    assert "Unsupported prop_schema" in str(exc_info.value)


def test_resolve_default():
    builder = importlib.import_module("framex.plugins.proxy.builder")
    resolve_default: Callable = getattr(builder, "resolve_default")

    assert resolve_default(int) == 0
    assert resolve_default(str) == ""
    assert resolve_default(list[int]) == []
    assert resolve_default(dict[str, int]) == {}
    assert resolve_default(set[int]) == set()
    assert resolve_default(Union[int, str]) == 0  # noqa
    assert resolve_default(Optional[int]) == 0  # noqa
    assert resolve_default(MatchMataConfig) == MatchMataConfig()

    with pytest.raises(RuntimeError) as exc_info:
        resolve_default(lambda x: x)
    assert "Cannot instantiate default" in str(exc_info.value)


# if __name__ == "__main__":
#     test_resolve_annotation()
