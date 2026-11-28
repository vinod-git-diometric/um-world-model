"""Acquire the pinned Places bbox via the official STAC index and HTTPS ranges."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import resource
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit

import httpx
import pyarrow.parquet as pq
from shapely import from_wkb
from shapely.geometry import mapping

from .business_first import BUCKET, CATALOG, RELEASE, boundary
from .physical_graph import digest

LIMIT = 32_000_000
BOUND_FIELDS = ("xmin", "ymin", "xmax", "ymax")
PLACE_COLUMNS = (
    "id",
    "geometry",
    "bbox",
    "names",
    "taxonomy",
    "basic_category",
    "addresses",
    "websites",
    "sources",
    "confidence",
    "operating_status",
)


def intersects(box, bounds):
    x0, y0, x1, y1 = bounds
    return (
        box["xmin"] <= x1
        and box["xmax"] >= x0
        and box["ymin"] <= y1
        and box["ymax"] >= y0
    )


class HTTPSRange(io.RawIOBase):
    def __init__(self, client, url, size):
        parsed = urlsplit(url)
        if (
            parsed.scheme != "https"
            or parsed.netloc != urlsplit(BUCKET).netloc
            or not parsed.path.startswith(
                f"/release/{RELEASE}/theme=places/type=place/"
            )
            or not parsed.path.endswith(".parquet")
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("STAC asset is outside the permitted pinned Places prefix")
        self.client, self.url, self.size = client, url, size
        self.position = 0
        self.etag = None
        self.receipts = []

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.position

    def seek(self, offset, whence=0):
        self.position = offset + (0, self.position, self.size)[whence]
        if self.position < 0:
            raise ValueError("Negative file position")
        return self.position

    def read(self, size=-1):
        size = max(0, min(self.size - self.position, self.size if size < 0 else size))
        if not size:
            return b""
        if size > LIMIT:
            raise ValueError(f"Unexpected Places range size {size}")
        byte_range = f"{self.position}-{self.position + size - 1}"
        headers = {"Range": f"bytes={byte_range}", "Accept-Encoding": "identity"}
        if self.etag:
            headers["If-Match"] = self.etag
        with self.client.stream("GET", self.url, headers=headers) as response:
            response.raise_for_status()
            etag = response.headers.get("etag")
            if (
                response.status_code != 206
                or response.headers.get("content-range")
                != f"bytes {byte_range}/{self.size}"
                or not etag
                or (self.etag and self.etag != etag)
            ):
                raise ValueError(
                    "Unexpected partial response or changing Places object"
                )
            content = bytearray()
            for chunk in response.iter_bytes():
                if len(content) + len(chunk) > size:
                    raise ValueError("Places response exceeded requested byte range")
                content.extend(chunk)
        if len(content) != size:
            raise ValueError("Truncated Places range")
        self.etag = etag
        self.position += size
        self.receipts.append(
            {
                "range": byte_range,
                "bytes": size,
                "sha256": hashlib.sha256(content).hexdigest(),
            }
        )
        return bytes(content)


def read_asset(stream: HTTPSRange, bounds):
    parquet = pq.ParquetFile(stream)
    positions = {
        parquet.metadata.row_group(0).column(i).path_in_schema: i
        for i in range(parquet.metadata.num_columns)
    }
    selected = []
    rows = []
    for number in range(parquet.num_row_groups):
        group = parquet.metadata.row_group(number)
        stats = {
            key: group.column(positions[f"bbox.{key}"]).statistics
            for key in BOUND_FIELDS
            if f"bbox.{key}" in positions
        }
        if len(stats) == 4 and all(
            s is not None and s.has_min_max for s in stats.values()
        ):
            envelope = {
                key: s.min if key.endswith("min") else s.max for key, s in stats.items()
            }
            if not intersects(envelope, bounds):
                continue
        selected.append(number)
        for row in parquet.read_row_group(
            number, columns=PLACE_COLUMNS, use_threads=False
        ).to_pylist():
            if row["bbox"] is not None and not intersects(row["bbox"], bounds):
                continue
            geometry = mapping(from_wkb(row.pop("geometry")))
            rows.append(
                {
                    "type": "Feature",
                    "id": row.pop("id"),
                    "geometry": geometry,
                    "properties": row,
                }
            )
    return rows, selected


def acquire(boundary_path: Path, output: Path):
    started, cpu = time.perf_counter(), time.process_time()
    bounds = boundary(boundary_path).bounds
    output.mkdir(parents=True, exist_ok=False)
    index_url = f"{CATALOG}/{RELEASE}/collections.parquet"
    index_path = output / "collections.parquet"
    data_path = output / "places.geojsonseq"
    receipts = []
    count = 0
    with httpx.Client(timeout=30, follow_redirects=False) as client:
        with client.stream("GET", index_url) as response, index_path.open("xb") as file:
            response.raise_for_status()
            if response.status_code != 200:
                raise ValueError("Expected full pinned STAC index")
            for chunk in response.iter_bytes():
                if file.tell() + len(chunk) > LIMIT:
                    raise ValueError("Unexpected STAC index size")
                file.write(chunk)
        index = pq.read_table(
            index_path, columns=["collection", "type", "bbox", "assets"]
        )
        with data_path.open("x", encoding="utf-8") as handle:
            for item in index.to_pylist():
                if (
                    item["type"] != "Feature"
                    or item["collection"] != "place"
                    or not intersects(item["bbox"], bounds)
                ):
                    continue
                asset = item["assets"]["aws"]
                stream = HTTPSRange(client, asset["href"], asset["file:size"])
                rows, groups = read_asset(stream, bounds)
                for row in rows:
                    handle.write(json.dumps(row, default=str) + "\n")
                count += len(rows)
                receipts.append(
                    {
                        "url": stream.url,
                        "etag": stream.etag,
                        "row_groups": groups,
                        "ranges": stream.receipts,
                    }
                )
    receipt = {
        "release": RELEASE,
        "completed_at": datetime.now(UTC).isoformat(),
        "stac_url": index_url,
        "stac_sha256": digest(index_path),
        "stac_bytes": index_path.stat().st_size,
        "boundary_sha256": digest(boundary_path),
        "bbox": bounds,
        "bbox_rows": count,
        "data_sha256": digest(data_path),
        "assets": receipts,
        "range_requests": sum(len(r["ranges"]) for r in receipts),
        "range_bytes": sum(g["bytes"] for r in receipts for g in r["ranges"]),
        "wall_seconds": time.perf_counter() - started,
        "cpu_seconds": time.process_time() - cpu,
        "max_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    (output / "receipt.json").write_text(
        json.dumps(receipt, indent=2), encoding="utf-8"
    )
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("boundary", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    receipt = acquire(args.boundary, args.output)
    print(json.dumps({k: v for k, v in receipt.items() if k != "assets"}, indent=2))


if __name__ == "__main__":
    main()
