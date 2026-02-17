import pytest

from app.core.chunk_mappings import (
    extract_chunk_mapping_fields,
    render_chunk_mapping,
)


def test_extract_chunk_mapping_fields_returns_expected_fields() -> None:
    fields = extract_chunk_mapping_fields(
        chunk_mappings="{field1} - {field2} / {nested.field3}, {field4}"
    )
    assert fields == {"field1", "field2", "nested.field3", "field4"}


def test_extract_chunk_mapping_fields_raises_on_invalid_placeholder() -> None:
    with pytest.raises(ValueError):
        extract_chunk_mapping_fields(chunk_mappings="{field 1} - {field2}")


def test_render_chunk_mapping_does_not_escape_field_values() -> None:
    rendered = render_chunk_mapping(
        chunk_mappings="{name} / {type}",
        source_record={"name": "O'Malley", "type": "artifact\\creature"},
    )
    assert rendered == "O'Malley / artifact\\creature"


def test_render_chunk_mapping_escapes_template_literal_segments() -> None:
    rendered = render_chunk_mapping(
        chunk_mappings="prefix ' {name}",
        source_record={"name": "value"},
    )
    assert rendered == "prefix '' value"
