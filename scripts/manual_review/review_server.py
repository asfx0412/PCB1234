#!/usr/bin/env python3
"""Local manual review server for generated UniPCB VQA data."""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import posixpath
import re
import tempfile
import threading
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_FILE = (
    PROJECT_ROOT
    / "data/benchmark/generated/generate_vqa_bilingual_test/all_vqa_data_bilingual_20260426_190307.json"
)
DEFAULT_REVIEW_FILE = (
    PROJECT_ROOT
    / "data/benchmark/generated/generate_vqa_bilingual_test/manual_review_20260426_190307.json"
)
STATIC_DIR = Path(__file__).resolve().parent / "static"
DEFAULT_REVIEWER = "reviewer1"


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json_atomic(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False
    ) as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")
        temp_name = f.name
    os.replace(temp_name, path)


def parse_coordinate_answer(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, str):
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, dict):
        return []

    boxes: list[dict[str, Any]] = []
    for label, coords in parsed.items():
        if not isinstance(coords, list):
            continue
        for coord in coords:
            if (
                isinstance(coord, list)
                and len(coord) == 4
                and all(isinstance(n, (int, float)) for n in coord)
            ):
                x1, y1, x2, y2 = coord
                boxes.append(
                    {
                        "label": str(label),
                        "x1": x1,
                        "y1": y1,
                        "x2": x2,
                        "y2": y2,
                    }
                )
    return boxes


def safe_reviewer_name(value: str | None) -> str:
    value = (value or DEFAULT_REVIEWER).strip()
    if not value:
        return DEFAULT_REVIEWER
    return re.sub(r"[^0-9A-Za-z_.-]+", "_", value)[:80] or DEFAULT_REVIEWER


class ReviewStore:
    def __init__(self, data_file: Path, review_file: Path, default_reviewer: str):
        self.data_file = data_file
        self.review_file = review_file
        self.data = read_json(data_file, [])
        self.default_reviewer = safe_reviewer_name(default_reviewer)
        self.reviews: dict[str, dict[str, Any]] = {}
        self.lock = threading.Lock()

    def review_path(self, reviewer: str) -> Path:
        reviewer = safe_reviewer_name(reviewer)
        if reviewer == self.default_reviewer:
            return self.review_file
        return self.review_file.with_name(
            f"{self.review_file.stem}_{reviewer}{self.review_file.suffix}"
        )

    def review_payload(self, reviewer: str) -> dict[str, Any]:
        reviewer = safe_reviewer_name(reviewer)
        if reviewer not in self.reviews:
            review_file = self.review_path(reviewer)
            self.reviews[reviewer] = read_json(
                review_file,
                {
                    "data_file": str(self.data_file),
                    "reviewer": reviewer,
                    "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "updated_at": None,
                    "items": {},
                },
            )
            self.reviews[reviewer].setdefault("items", {})
            self.reviews[reviewer]["reviewer"] = reviewer
        return self.reviews[reviewer]

    def review_key(self, record_index: int, qa_index: int) -> str:
        return f"{record_index}:{qa_index}"

    def summary(self, reviewer: str) -> dict[str, Any]:
        reviewer = safe_reviewer_name(reviewer)
        review = self.review_payload(reviewer)
        qa_total = sum(len(record.get("conversation", [])) for record in self.data)
        items = review.get("items", {})
        problem_count = sum(1 for item in items.values() if item.get("status") == "problem")
        ok_count = sum(1 for item in items.values() if item.get("status") == "ok")
        return {
            "records": len(self.data),
            "qa_total": qa_total,
            "reviewed": len(items),
            "ok": ok_count,
            "problem": problem_count,
            "reviewer": reviewer,
            "review_file": str(self.review_path(reviewer)),
            "data_file": str(self.data_file),
        }

    def record_overview(self, reviewer: str, offset: int = 0, limit: int = 300) -> dict[str, Any]:
        review = self.review_payload(reviewer)
        items = review.get("items", {})
        records = []
        total = len(self.data)
        offset = max(0, min(offset, total))
        limit = max(1, min(limit, 1000))
        end = min(total, offset + limit)
        for record_index in range(offset, end):
            record = self.data[record_index]
            qa_total = len(record.get("conversation", []))
            ok = 0
            problem = 0
            for qa_index in range(qa_total):
                item = items.get(self.review_key(record_index, qa_index))
                if item and item.get("status") == "ok":
                    ok += 1
                elif item and item.get("status") == "problem":
                    problem += 1
            reviewed = ok + problem
            if problem:
                status = "problem"
            elif reviewed == 0:
                status = "unreviewed"
            elif reviewed == qa_total:
                status = "complete"
            else:
                status = "partial"
            records.append(
                {
                    "record_index": record_index,
                    "qa_total": qa_total,
                    "reviewed": reviewed,
                    "ok": ok,
                    "problem": problem,
                    "status": status,
                    "dataset": record.get("dataset"),
                    "language": record.get("language"),
                }
            )
        return {
            "records": records,
            "offset": offset,
            "limit": limit,
            "total": total,
            "summary": self.summary(reviewer),
        }

    def record_payload(self, record_index: int, reviewer: str) -> dict[str, Any]:
        if record_index < 0 or record_index >= len(self.data):
            raise IndexError(record_index)

        review = self.review_payload(reviewer)
        record = self.data[record_index]
        conversations = []
        for qa_index, qa in enumerate(record.get("conversation", [])):
            enriched = dict(qa)
            enriched["qa_index"] = qa_index
            enriched["review"] = review["items"].get(
                self.review_key(record_index, qa_index)
            )
            enriched["boxes"] = parse_coordinate_answer(qa.get("correct_option"))
            conversations.append(enriched)

        images = []
        for image_path in record.get("images", []):
            images.append(
                {
                    "path": image_path,
                    "url": f"/image?path={image_path}",
                    "exists": self.resolve_project_path(image_path).exists(),
                }
            )

        return {
            "record_index": record_index,
            "record_count": len(self.data),
            "dataset": record.get("dataset"),
            "dataset_type": record.get("dataset_type"),
            "language": record.get("language"),
            "image_size": record.get("image_size"),
            "images": images,
            "conversation": conversations,
        }

    def save_item(self, item: dict[str, Any], reviewer: str) -> dict[str, Any]:
        reviewer = safe_reviewer_name(reviewer)
        record_index = int(item["record_index"])
        qa_index = int(item["qa_index"])
        if record_index < 0 or record_index >= len(self.data):
            raise IndexError(record_index)
        if qa_index < 0 or qa_index >= len(self.data[record_index].get("conversation", [])):
            raise IndexError(qa_index)

        status = item.get("status")
        if status not in {"ok", "problem", "unreviewed"}:
            raise ValueError("status must be ok, problem, or unreviewed")

        with self.lock:
            review = self.review_payload(reviewer)
            key = self.review_key(record_index, qa_index)
            if status == "unreviewed":
                review["items"].pop(key, None)
            else:
                review["items"][key] = {
                    "record_index": record_index,
                    "qa_index": qa_index,
                    "status": status,
                    "note": str(item.get("note", "")).strip(),
                    "reviewer": reviewer,
                    "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                }
            review["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            write_json_atomic(self.review_path(reviewer), review)
        return {"ok": True, "summary": self.summary(reviewer)}

    def resolve_project_path(self, raw_path: str) -> Path:
        candidate = (PROJECT_ROOT / raw_path).resolve()
        root = PROJECT_ROOT.resolve()
        if root != candidate and root not in candidate.parents:
            raise ValueError("path outside project root")
        return candidate


class ReviewHandler(BaseHTTPRequestHandler):
    store: ReviewStore

    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"[review] {self.address_string()} - {fmt % args}")

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        reviewer = safe_reviewer_name(query.get("reviewer", [DEFAULT_REVIEWER])[0])
        try:
            if parsed.path == "/":
                self.serve_static("index.html")
            elif parsed.path.startswith("/static/"):
                self.serve_static(parsed.path.removeprefix("/static/"))
            elif parsed.path == "/api/meta":
                self.send_json(self.store.summary(reviewer))
            elif parsed.path == "/api/records":
                offset = int(query.get("offset", ["0"])[0])
                limit = int(query.get("limit", ["300"])[0])
                self.send_json(self.store.record_overview(reviewer, offset, limit))
            elif parsed.path.startswith("/api/record/"):
                record_index = int(parsed.path.rsplit("/", 1)[-1])
                self.send_json(self.store.record_payload(record_index, reviewer))
            elif parsed.path == "/image":
                raw_path = query.get("path", [""])[0]
                self.serve_image(raw_path)
            else:
                self.send_error(HTTPStatus.NOT_FOUND)
        except (IndexError, ValueError) as exc:
            self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
        except Exception as exc:  # pragma: no cover - keeps local tool debuggable.
            self.send_json({"error": repr(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/api/review":
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        try:
            query = parse_qs(parsed.query)
            reviewer = safe_reviewer_name(query.get("reviewer", [DEFAULT_REVIEWER])[0])
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length)
            payload = json.loads(body.decode("utf-8"))
            self.send_json(self.store.save_item(payload, reviewer))
        except (json.JSONDecodeError, KeyError, IndexError, ValueError) as exc:
            self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)

    def send_json(self, payload: Any, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def serve_static(self, relative: str) -> None:
        safe = posixpath.normpath(unquote(relative)).lstrip("/")
        path = (STATIC_DIR / safe).resolve()
        static_root = STATIC_DIR.resolve()
        if static_root != path and static_root not in path.parents:
            self.send_error(HTTPStatus.FORBIDDEN)
            return
        if not path.exists() or not path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        self.send_file(path)

    def serve_image(self, raw_path: str) -> None:
        path = self.store.resolve_project_path(raw_path)
        if not path.exists() or not path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        self.send_file(path)

    def send_file(self, path: Path) -> None:
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        body = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serve a local UniPCB VQA manual review UI.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8008)
    parser.add_argument("--data-file", type=Path, default=DEFAULT_DATA_FILE)
    parser.add_argument("--review-file", type=Path, default=DEFAULT_REVIEW_FILE)
    parser.add_argument("--reviewer", default=DEFAULT_REVIEWER)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ReviewHandler.store = ReviewStore(
        args.data_file.resolve(), args.review_file.resolve(), args.reviewer
    )
    try:
        server = ThreadingHTTPServer((args.host, args.port), ReviewHandler)
    except OSError as exc:
        if exc.errno == 98:
            print(
                f"Port {args.port} is already in use. Open http://{args.host}:{args.port} "
                f"if the review UI is already running, or restart with another port, for example:\n"
                f"python scripts/manual_review/review_server.py --host {args.host} --port {args.port + 1}"
            )
            return
        raise
    print(f"Manual review UI: http://{args.host}:{args.port}")
    print(f"Data file: {args.data_file}")
    print(f"Default reviewer: {safe_reviewer_name(args.reviewer)}")
    print(f"Review output: {ReviewHandler.store.review_path(args.reviewer)}")
    server.serve_forever()


if __name__ == "__main__":
    main()
