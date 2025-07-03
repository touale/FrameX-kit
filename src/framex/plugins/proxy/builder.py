from typing import Any

from pydantic import BaseModel, create_model

_created_models: dict[str, type[BaseModel]] = {}

type_map = {
    "string": str,
    "integer": int,
    "number": float,
    "boolean": bool,
    "array": list,
    "object": dict,
}


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
        if "$ref" in prop_schema:
            # Nested $ref support
            ref = prop_schema["$ref"]
            ref_name = ref.split("/")[-1]
            nested_schema = components.get(ref_name)
            if nested_schema is None:
                raise ValueError(f"Missing schema for ref: {ref_name}")
            nested_model = create_pydantic_model(ref_name, nested_schema, components)
            annotation = nested_model
        else:
            typ = prop_schema.get("type", "string")
            annotation = type_map.get(typ, str)

        required = field_name in required_fields
        default = ... if required else None
        fields[field_name] = (annotation, default)

    model: type[BaseModel] = create_model(name, **fields)  # type: ignore
    _created_models[name] = model
    return model
