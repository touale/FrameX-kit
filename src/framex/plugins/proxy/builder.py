from typing import Any, Union

from pydantic import BaseModel, create_model

_created_models: dict[str, type[BaseModel]] = {}

type_map = {
    "string": str,
    "integer": int,
    "number": float,
    "boolean": bool,
    "array": list,
    "object": dict,
    "null": None,
}
from typing import get_args, get_origin


def resolve_annotation(
    prop_schema: dict,
    components: dict,
) -> Any:
    if "$ref" in prop_schema:
        # Nested $ref support
        ref = prop_schema["$ref"]
        ref_name = ref.split("/")[-1]
        if nested_schema := components.get(ref_name):
            return create_pydantic_model(ref_name, nested_schema, components)
    if "anyOf" in prop_schema:
        options = []
        for option_schema in prop_schema["anyOf"]:
            typ = option_schema.get("type")
            if typ == "array":
                item_type = type_map.get(option_schema.get("items", {}).get("type", "string"), str)
                options.append(list[item_type])  # type: ignore [valid-type]
            else:
                options.append(type_map.get(typ, str))  # type: ignore [arg-type]
        return Union[*options]
    typ = prop_schema.get("type")
    if typ == "array":
        prop_schema = prop_schema.get("items", {})
        if "$ref" in prop_schema:
            item_type = resolve_annotation(prop_schema, components)
        else:
            item_type = type_map.get(prop_schema.get("type", "string"), str)
        return list[item_type]  # type: ignore [valid-type]
    if typ:
        return type_map.get(typ, str)
    raise RuntimeError(f"Unsupported prop_schema: {prop_schema}")


def resolve_default(annotation: Any) -> Any:
    origin = get_origin(annotation)
    # Union type support: try the first type that can construct a default value first
    if origin is Union and (args := get_args(annotation)) and len(args) > 1:
        return resolve_default(args[0])
    if origin in (list, dict, set):
        return origin()
    if isinstance(annotation, type):
        return annotation()
    raise RuntimeError(f"Cannot instantiate default for unsupported type: {annotation}")


def reset_created_models() -> None:
    """Reset the created models cache."""
    global _created_models
    _created_models = {}


def create_pydantic_model(
    name: str,
    schema: dict,
    components: dict,
) -> type[BaseModel]:
    if name in _created_models:
        return _created_models[name]
    fields: dict[str, tuple[Any, Any]] = {}
    props = schema.get("properties", {})
    required_fields = schema.get("required", [])
    for field_name, prop_schema in props.items():
        # Get annotation
        annotation = resolve_annotation(prop_schema, components)
        # Get default value
        if field_name in required_fields:
            default = ...
        elif "default" in prop_schema:
            default = prop_schema["default"]
        else:
            default = resolve_default(annotation)  # pragma: no cover
        fields[field_name] = (annotation, default)
    model: type[BaseModel] = create_model(name, **fields)  # type: ignore
    _created_models[name] = model
    return model
