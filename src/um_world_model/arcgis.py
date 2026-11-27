"""Small ArcGIS FeatureServer client with explicit pagination and reconciliation."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any, Self

import httpx


class ArcGISError(RuntimeError):
    pass


@dataclass(frozen=True)
class Page:
    offset: int
    features: list[dict[str, Any]]
    response: dict[str, Any]


class ArcGISClient:
    def __init__(
        self, timeout: float = 60.0, transport: httpx.BaseTransport | None = None
    ):
        self.client = httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            transport=transport,
            headers={"User-Agent": "um-world-model/0.1 public-data-research"},
        )

    def close(self) -> None:
        self.client.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def get_json(
        self, url: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        response = self.client.get(url, params=params)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ArcGISError(f"expected JSON object from {response.url}")
        if "error" in payload:
            raise ArcGISError(f"ArcGIS error from {response.url}: {payload['error']}")
        return payload

    def layer_metadata(self, layer_url: str) -> dict[str, Any]:
        return self.get_json(layer_url, {"f": "json"})

    def count(self, layer_url: str, where: str) -> int:
        payload = self.get_json(
            f"{layer_url.rstrip('/')}/query",
            {"f": "json", "where": where, "returnCountOnly": "true"},
        )
        if "count" not in payload:
            raise ArcGISError("count query returned no count")
        return int(payload["count"])

    def pages(
        self,
        layer_url: str,
        where: str,
        *,
        out_fields: str = "*",
        page_size: int | None = None,
        return_geometry: bool = True,
    ) -> Iterable[Page]:
        metadata = self.layer_metadata(layer_url)
        object_id = metadata.get("objectIdField") or metadata.get("objectIdFieldName")
        if not object_id:
            raise ArcGISError("layer metadata has no object ID field")
        maximum = int(metadata.get("maxRecordCount") or 1000)
        size = min(page_size or maximum, maximum)
        expected = self.count(layer_url, where)
        offset = 0
        seen_ids: set[Any] = set()
        while offset < expected:
            payload = self.get_json(
                f"{layer_url.rstrip('/')}/query",
                {
                    "f": "json",
                    "where": where,
                    "outFields": out_fields,
                    "returnGeometry": str(return_geometry).lower(),
                    "resultOffset": offset,
                    "resultRecordCount": size,
                    "orderByFields": f"{object_id} ASC",
                    "outSR": 4326,
                },
            )
            features = payload.get("features")
            if not isinstance(features, list):
                raise ArcGISError(f"query at offset {offset} returned no feature list")
            if not features:
                raise ArcGISError(f"pagination stopped at {offset} of {expected}")
            for feature in features:
                oid = feature.get("attributes", {}).get(object_id)
                if oid in seen_ids:
                    raise ArcGISError(f"duplicate object ID during pagination: {oid}")
                seen_ids.add(oid)
            yield Page(offset=offset, features=features, response=payload)
            offset += len(features)
        if len(seen_ids) != expected:
            raise ArcGISError(
                f"count mismatch: expected {expected}, received {len(seen_ids)}"
            )


def field_lookup(metadata: dict[str, Any]) -> dict[str, str]:
    return {
        str(field["name"]).upper(): str(field["name"])
        for field in metadata.get("fields", [])
    }


def choose_field(
    metadata: dict[str, Any], candidates: list[str], *, required: bool = True
) -> str | None:
    lookup = field_lookup(metadata)
    for candidate in candidates:
        if candidate.upper() in lookup:
            return lookup[candidate.upper()]
    if required:
        raise ArcGISError(f"none of the expected fields exist: {', '.join(candidates)}")
    return None


def sql_string(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def find_feature_layer_url(item: dict[str, Any], item_data: dict[str, Any]) -> str:
    direct = item.get("url")
    if isinstance(direct, str) and "FeatureServer" in direct:
        return direct.rstrip("/") + (
            "/0" if direct.rstrip("/").endswith("FeatureServer") else ""
        )
    candidates: list[str] = []
    for layer in item_data.get("layers", []):
        if isinstance(layer, dict) and isinstance(layer.get("url"), str):
            candidates.append(layer["url"])
    for service in item_data.get("operationalLayers", []):
        if isinstance(service, dict) and isinstance(service.get("url"), str):
            candidates.append(service["url"])
    for url in candidates:
        if "FeatureServer" in url:
            return url.rstrip("/") + (
                "/0" if url.rstrip("/").endswith("FeatureServer") else ""
            )
    raise ArcGISError("ArcGIS item does not identify a feature layer URL")
