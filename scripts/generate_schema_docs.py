"""Generate Markdown documentation tables from Cordra JSON schemas."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMAS_DIR = PROJECT_ROOT / "schemas"
DOCS_DIR = PROJECT_ROOT / "docs"
MKDOCS_FILE = PROJECT_ROOT / "mkdocs.yml"

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


def generate_docs(schema_paths: list[Path]) -> list[Path]:
    """Generate one Markdown file per ``*.schema.json`` file.

    Top-level Markdown files in ``DOCS_DIR`` that do not match a schema in
    ``SCHEMAS_DIR`` are removed.
    """
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    expected_paths = {
        DOCS_DIR / f"{_schema_slug(schema_path)}.md"
        for schema_path in schema_paths
    }

    _remove_stale_docs(expected_paths)

    for schema_path in schema_paths:
        with schema_path.open("r", encoding="utf-8") as schema_file:
            schema = json.load(schema_file)

        output_path = DOCS_DIR / f"{_schema_slug(schema_path)}.md"
        output_path.write_text(schema_to_markdown(schema), encoding="utf-8")
        written.append(output_path)
    return written


def schema_paths() -> list[Path]:
    return sorted(SCHEMAS_DIR.glob("*.schema.json"))


def _remove_stale_docs(expected_paths: set[Path]) -> None:
    for markdown_path in DOCS_DIR.glob("*.md"):
        if markdown_path not in expected_paths:
            markdown_path.unlink()


def update_mkdocs_nav(schema_paths: list[Path]) -> None:
    """Replace the MkDocs nav block with pages generated from schemas."""
    nav_lines = ["nav:\n"]
    nav_lines.extend(
        f"  - {_schema_nav_label(schema_path)}: {_schema_slug(schema_path)}.md\n"
        for schema_path in schema_paths
    )

    original = MKDOCS_FILE.read_text(encoding="utf-8")
    lines = original.splitlines(keepends=True)
    nav_start = _find_nav_start(lines)

    if nav_start is None:
        separator = "" if original.endswith("\n") or not original else "\n"
        MKDOCS_FILE.write_text(
            f"{original}{separator}\n{''.join(nav_lines)}",
            encoding="utf-8",
        )
        return

    nav_end = _find_nav_end(lines, nav_start)
    lines[nav_start:nav_end] = nav_lines
    MKDOCS_FILE.write_text("".join(lines), encoding="utf-8")


def _find_nav_start(lines: list[str]) -> int | None:
    for index, line in enumerate(lines):
        if line.strip() == "nav:" and not line.startswith((" ", "\t")):
            return index
    return None


def _find_nav_end(lines: list[str], nav_start: int) -> int:
    for index in range(nav_start + 1, len(lines)):
        line = lines[index]
        if line.strip() and not line.startswith((" ", "\t")):
            return index
    return len(lines)


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
    words = _schema_words(schema_path)
    return "-".join(word.lower() for word in words) or name.lower()


def _schema_nav_label(schema_path: Path) -> str:
    words = _schema_words(schema_path)
    return " ".join(_uppercase_first_letter(word) for word in words)


def _schema_words(schema_path: Path) -> list[str]:
    name = schema_path.name.removesuffix(".schema.json")
    return re.findall(r"[A-Z]+(?=[A-Z][a-z]|$)|[A-Z]?[a-z]+|\d+", name)


def _uppercase_first_letter(word: str) -> str:
    return f"{word[:1].upper()}{word[1:]}"


def _escape_cell(value: Any) -> str:
    return str(value).replace("\n", " ").replace("|", "\\|")


def main() -> int:
    discovered_schema_paths = schema_paths()
    written = generate_docs(discovered_schema_paths)
    update_mkdocs_nav(discovered_schema_paths)
    for path in written:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
