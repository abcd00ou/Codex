from __future__ import annotations

import json
from copy import deepcopy
from datetime import date, datetime
from pathlib import Path
from typing import Any


class LocalCursor:
    def __init__(self, documents: list[dict[str, Any]]):
        self.documents = documents

    def sort(self, key_or_list: Any, direction: Any = None) -> "LocalCursor":
        if isinstance(key_or_list, list):
            key, direction = key_or_list[0]
        else:
            key = key_or_list

        reverse = direction == -1
        if isinstance(direction, dict):
            reverse = True

        self.documents.sort(key=lambda item: _get_nested(item, key) or "", reverse=reverse)
        return self

    def limit(self, value: int) -> "LocalCursor":
        self.documents = self.documents[:value]
        return self

    def __iter__(self):
        return iter(self.documents)


class LocalCollection:
    def __init__(self, database: "LocalDatabase", name: str):
        self.database = database
        self.name = name

    @property
    def records(self) -> list[dict[str, Any]]:
        return self.database.data.setdefault(self.name, [])

    def create_index(self, *args: Any, **kwargs: Any) -> None:
        return None

    def insert_one(self, document: dict[str, Any]) -> None:
        self.records.append(_json_safe(document))
        self.database.save()

    def insert_many(self, documents: list[dict[str, Any]]) -> None:
        self.records.extend(_json_safe(document) for document in documents)
        self.database.save()

    def replace_one(self, query: dict[str, Any], document: dict[str, Any], upsert: bool = False) -> None:
        for index, record in enumerate(self.records):
            if _matches(record, query):
                self.records[index] = _json_safe(document)
                self.database.save()
                return
        if upsert:
            self.records.append(_json_safe(document))
            self.database.save()

    def find_one(
        self,
        query: dict[str, Any],
        projection: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        for record in self.records:
            if _matches(record, query):
                return _project(record, projection)
        return None

    def find(
        self,
        query: dict[str, Any] | None = None,
        projection: dict[str, Any] | None = None,
    ) -> LocalCursor:
        query = query or {}
        records = []
        for record in self.records:
            if _matches(record, query):
                projected = _project(record, projection)
                if "$text" in query:
                    projected["score"] = _text_score(record, query["$text"].get("$search", ""))
                records.append(projected)
        return LocalCursor(records)

    def count_documents(self, query: dict[str, Any]) -> int:
        return sum(1 for record in self.records if _matches(record, query))


class LocalDatabase:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.data = self._load()

    def __getattr__(self, name: str) -> LocalCollection:
        return LocalCollection(self, name)

    def _load(self) -> dict[str, list[dict[str, Any]]]:
        if not self.path.exists():
            return {}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def save(self) -> None:
        self.path.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, datetime | date):
        return value.isoformat()
    return deepcopy(value)


def _matches(record: dict[str, Any], query: dict[str, Any]) -> bool:
    if not query:
        return True
    if "$text" in query:
        return _text_score(record, query["$text"].get("$search", "")) > 0
    return all(_get_nested(record, key) == value for key, value in query.items())


def _text_score(record: dict[str, Any], query: str) -> int:
    haystack = json.dumps(record, ensure_ascii=False).lower()
    terms = [term.lower() for term in query.split() if term.strip()]
    if not terms:
        return 0
    return sum(haystack.count(term) for term in terms)


def _project(
    record: dict[str, Any],
    projection: dict[str, Any] | None,
) -> dict[str, Any]:
    item = deepcopy(record)
    if not projection:
        return item

    excludes = {key for key, value in projection.items() if value == 0}
    includes = {key for key, value in projection.items() if value == 1}

    if includes:
        item = {}
        for key in includes:
            value = _get_nested(record, key)
            if value is not None:
                _set_nested(item, key, value)

    for key in excludes:
        _remove_nested(item, key)
    return item


def _get_nested(record: dict[str, Any], key: str) -> Any:
    current: Any = record
    for part in key.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def _remove_nested(record: dict[str, Any], key: str) -> None:
    parts = key.split(".")
    current = record
    for part in parts[:-1]:
        current = current.get(part, {})
        if not isinstance(current, dict):
            return
    current.pop(parts[-1], None)


def _set_nested(record: dict[str, Any], key: str, value: Any) -> None:
    parts = key.split(".")
    current = record
    for part in parts[:-1]:
        current = current.setdefault(part, {})
    current[parts[-1]] = value
