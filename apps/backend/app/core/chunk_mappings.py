import re
from typing import Any, Dict

from app.models.db import MongoCollectionRecord

FIELD_TOKEN_PATTERN = re.compile(r"\{([A-Za-z_][A-Za-z0-9_.]*)\}")


def extract_chunk_mapping_fields(*, chunk_mappings: str) -> set[str]:
    _validate_chunk_mapping_syntax(chunk_mappings=chunk_mappings)
    return set(FIELD_TOKEN_PATTERN.findall(chunk_mappings))


def render_chunk_mapping(
    source_record: MongoCollectionRecord, chunk_mappings: str
) -> str:
    _validate_chunk_mapping_syntax(chunk_mappings=chunk_mappings)

    output_parts: list[str] = []
    current_pos = 0
    for match in FIELD_TOKEN_PATTERN.finditer(chunk_mappings):
        start, end = match.span()
        literal_segment = chunk_mappings[current_pos:start]
        field_name = match.group(1)

        output_parts.append(escape_template_literal(value=literal_segment))

        field_value = _get_nested_value(source_record, field_name=field_name)
        output_parts.append("" if field_value is None else str(field_value))
        current_pos = end

    output_parts.append(escape_template_literal(value=chunk_mappings[current_pos:]))
    return "".join(output_parts)


def escape_template_literal(*, value: str) -> str:
    # Escapes characters commonly used to break out of SQL string literals.
    return (
        value.replace("\\", "\\\\")
        .replace("'", "''")
        .replace('"', '\\"')
        .replace("\x00", "")
        .replace("\n", "\\n")
        .replace("\r", "\\r")
    )


def _validate_chunk_mapping_syntax(*, chunk_mappings: str) -> None:
    cleaned = FIELD_TOKEN_PATTERN.sub("", chunk_mappings)
    if "{" in cleaned or "}" in cleaned:
        raise ValueError(
            "Invalid chunk_mappings syntax. Use placeholders like {field_name}."
        )


def _get_nested_value(
    source_record: MongoCollectionRecord, *, field_name: str
) -> Any | None:
    current: Dict[str, Any] | None = source_record.model_dump()
    for part in field_name.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current
