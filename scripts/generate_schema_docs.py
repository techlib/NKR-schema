"""Generate Markdown documentation tables from Cordra JSON schemas."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


TABLE_HEADER = "id | name | data type | cardinality | description"
TABLE_SEPARATOR = "-- | -- | -- | -- | --"

# Direct JSON Schema -> documentation mappings. Rules that need context
# (arrays, enums, and Cordra extensions) are applied explicitly below.
JSON_TYPE_TO_DOCUMENTATION_TYPE = {
    "string": "string",
    "number": "number",
    "integer": "integer",
    "boolean": "boolean",
    "object": "object",
    "null": "null",
}
STRING_FORMAT_TO_DOCUMENTATION_TYPE = {
    "uri": "uri",
    "email": "email",
    "date": "date",
}
JSON_TYPE_TO_MAXIMUM_CARDINALITY = {
    "array": "n",
}


@dataclass(frozen=True)
class FieldRow:
    field_id: str
    name: str
    data_type: str
    cardinality: str
    description: str

    def to_markdown(self) -> str:
        return " | ".join(
            [
                _escape_cell(self.field_id),
                _escape_cell(self.name),
                _escape_cell(self.data_type),
                _escape_cell(self.cardinality),
                _escape_cell(self.description),
            ]
        )


def schema_to_markdown(schema: dict[str, Any]) -> str:
    """Convert one JSON schema object to a Markdown table."""
    rows = list(iter_field_rows(schema))
    lines = [TABLE_HEADER, TABLE_SEPARATOR]
    lines.extend(row.to_markdown() for row in rows)
    return "\n".join(lines) + "\n"


def iter_field_rows(schema: dict[str, Any]) -> Iterable[FieldRow]:
    """Transform top-level and nested schema properties into field rows."""
    required = set(schema.get("required", []))
    yield from _iter_properties(schema.get("properties", {}), required, parent_id="")


def generate_docs(
    schemas_dir: Path,
    docs_dir: Path,
    overwrite: bool = True,
) -> list[Path]:
    """Generate one Markdown file per ``*.schema.json`` file."""
    docs_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for schema_path in sorted(schemas_dir.glob("*.schema.json")):
        with schema_path.open("r", encoding="utf-8") as schema_file:
            schema = json.load(schema_file)

        output_path = docs_dir / f"{_schema_slug(schema_path)}.md"
        if output_path.exists() and not overwrite:
            continue

        output_path.write_text(schema_to_markdown(schema), encoding="utf-8")
        written.append(output_path)
    return written


def _iter_properties(
    properties: dict[str, Any],
    required: set[str],
    parent_id: str,
) -> Iterable[FieldRow]:
    for property_name, property_schema in properties.items():
        field_id = f"{parent_id}.{property_name}" if parent_id else property_name
        yield property_to_field_row(
            property_name=property_name,
            property_schema=property_schema,
            required=required,
            field_id=field_id,
        )

        nested_schema = _nested_object_schema(property_schema)
        if nested_schema is not None:
            nested_required = set(nested_schema.get("required", []))
            yield from _iter_properties(
                nested_schema.get("properties", {}),
                nested_required,
                parent_id=field_id,
            )


def property_to_field_row(
    property_name: str,
    property_schema: dict[str, Any],
    required: set[str],
    field_id: str | None = None,
) -> FieldRow:
    """Transform one JSON Schema property into one documentation row."""
    return FieldRow(
        field_id=field_id or property_name,
        name=property_schema.get("title", property_name),
        data_type=documentation_data_type(property_schema),
        cardinality=documentation_cardinality(
            property_name,
            property_schema,
            required,
        ),
        description=property_schema.get("description", ""),
    )


def _nested_object_schema(schema: dict[str, Any]) -> dict[str, Any] | None:
    if schema.get("type") == "object":
        return schema
    if schema.get("type") == "array" and schema.get("items", {}).get("type") == "object":
        return schema["items"]
    return None


def documentation_data_type(schema: dict[str, Any]) -> str:
    """Transform a JSON Schema/Cordra type definition to its table value.

    Transformation priority:
    array -> item type, Cordra reference -> handle reference,
    enum -> enum, known string format -> format name, JSON type -> same name.
    """
    if schema.get("type") == "array":
        return documentation_data_type(schema.get("items", {}))
    if _is_handle_reference(schema):
        return "handle reference"
    if "enum" in schema:
        return "enum"

    json_type = schema.get("type", "")
    schema_format = schema.get("format")
    if json_type == "string" and schema_format in STRING_FORMAT_TO_DOCUMENTATION_TYPE:
        return STRING_FORMAT_TO_DOCUMENTATION_TYPE[schema_format]
    return JSON_TYPE_TO_DOCUMENTATION_TYPE.get(json_type, json_type or "unknown")


def documentation_cardinality(
    property_name: str,
    schema: dict[str, Any],
    required: set[str],
) -> str:
    """Transform schema occurrence rules to ``minimum..maximum``."""
    is_required = (
        property_name in required
        or _is_cordra_generated(schema)
        or bool(schema.get("readOnly"))
    )
    minimum = "1" if is_required else "0"
    maximum = JSON_TYPE_TO_MAXIMUM_CARDINALITY.get(schema.get("type"), "1")
    return f"{minimum}..{maximum}"


def _is_handle_reference(schema: dict[str, Any]) -> bool:
    return bool(
        schema.get("cordra", {})
        .get("type", {})
        .get("handleReference")
    )


def _is_cordra_generated(schema: dict[str, Any]) -> bool:
    return bool(
        schema.get("cordra", {})
        .get("type", {})
        .get("autoGeneratedField")
    )


def _schema_slug(schema_path: Path) -> str:
    name = schema_path.name.removesuffix(".schema.json")
    words = re.findall(r"[A-Z]+(?=[A-Z][a-z]|$)|[A-Z]?[a-z]+|\d+", name)
    return "-".join(word.lower() for word in words) or name.lower()


def _escape_cell(value: Any) -> str:
    return str(value).replace("\n", " ").replace("|", "\\|")


def _parse_args() -> argparse.Namespace:
    project_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(
        description="Generate Markdown documentation from Cordra JSON schemas."
    )
    parser.add_argument(
        "--schemas-dir",
        type=Path,
        default=project_root / "schemas" / "v1.0.0",
        help="Directory with *.schema.json files.",
    )
    parser.add_argument(
        "--docs-dir",
        type=Path,
        default=project_root / "docs",
        help="Directory where Markdown files will be written.",
    )
    parser.add_argument(
        "--no-overwrite",
        action="store_true",
        help="Create missing Markdown files only and keep existing files unchanged.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    written = generate_docs(
        schemas_dir=args.schemas_dir,
        docs_dir=args.docs_dir,
        overwrite=not args.no_overwrite,
    )
    for path in written:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
