from typing import Annotated, Any, Union, get_args, get_origin

from fastapi import File, Form, UploadFile
from pydantic import BaseModel, create_model

from framex.plugins.proxy.model import ProxyFuncHttpBody
from framex.utils import cache_decode

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


def unwrap_annotation(annotation: Any) -> Any:
    if get_origin(annotation) is Annotated:
        return get_args(annotation)[0]
    return annotation


def is_upload_annotation(annotation: Any) -> bool:
    annotation = unwrap_annotation(annotation)
    origin = get_origin(annotation)
    if origin is list:
        args = get_args(annotation)
        return len(args) == 1 and is_upload_annotation(args[0])
    return annotation is UploadFile


def to_multipart_annotation(annotation: Any) -> Any:
    if is_upload_annotation(annotation):
        return Annotated[annotation, File(...)]
    return Annotated[annotation, Form(...)]


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
        options: list[Any] = []
        for option_schema in prop_schema["anyOf"]:
            typ = option_schema.get("type")
            if typ == "array":
                item_type = type_map.get(option_schema.get("items", {}).get("type", "string"), str)
                options.append(list[item_type])  # type: ignore [valid-type]
            elif typ == "null":
                options.append(type(None))
            elif (
                (ref := option_schema.get("$ref"))
                and (ref_name := ref.split("/")[-1])
                and (nested_schema := components.get(ref_name))
            ):
                model = create_pydantic_model(ref_name, nested_schema, components)
                options.append(model)
            else:
                options.append(type_map.get(typ, str))  # type: ignore [arg-type]
        return Union[*options]
    typ = prop_schema.get("type")
    if typ == "array":
        prop_schema = prop_schema.get("items", {})
        if "$ref" in prop_schema:
            item_type = resolve_annotation(prop_schema, components)
        else:
            if prop_schema.get("type") == "string" and (
                prop_schema.get("contentMediaType") == "application/octet-stream"
                or prop_schema.get("format") == "binary"
            ):
                return list[UploadFile]  # type: ignore [valid-type]
            item_type = type_map.get(prop_schema.get("type", "string"), str)
        return list[item_type]  # type: ignore [valid-type]
    if typ:
        if typ == "string" and (
            prop_schema.get("contentMediaType") == "application/octet-stream" or prop_schema.get("format") == "binary"
        ):
            return UploadFile
        return type_map.get(typ, str)
    raise RuntimeError(f"Unsupported prop_schema: {prop_schema}")


def resolve_default(annotation: Any) -> Any:
    origin = get_origin(annotation)
    # Union type support: try the first type that can construct a default value first
    if origin is Union and (args := get_args(annotation)) and len(args) > 1:
        # If Union includes NoneType, return None
        if type(None) in args:
            return None
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


def format_proxy_params(**kwargs: Any) -> str:
    if (model := kwargs.get("model")) and isinstance(model, ProxyFuncHttpBody):
        func_name = cache_decode(model.func_name)
        data = cache_decode(model.data)
        return str({"func_name": func_name, "data": data})
    return str(kwargs)
