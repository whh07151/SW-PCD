#!/usr/bin/env python3
"""Validate tracked PDF and PowerPoint project artifacts without dependencies."""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path


def validate_pdf(path: Path) -> None:
    data = path.read_bytes()
    if not data.startswith(b"%PDF-"):
        raise ValueError("missing PDF header")
    if b"%%EOF" not in data[-65_536:]:
        raise ValueError("missing PDF end marker")


def validate_pptx(path: Path) -> None:
    with zipfile.ZipFile(path) as archive:
        corrupt_member = archive.testzip()
        if corrupt_member is not None:
            raise ValueError(f"corrupt ZIP member: {corrupt_member}")
        names = set(archive.namelist())
        required = {"[Content_Types].xml", "ppt/presentation.xml"}
        missing = sorted(required - names)
        if missing:
            raise ValueError(f"missing PowerPoint members: {', '.join(missing)}")


def validate_repository(root: Path) -> int:
    documents = sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in {".pdf", ".pptx"}
    )
    if not documents:
        print("No PDF or PPTX documents found.", file=sys.stderr)
        return 1

    failures: list[str] = []
    for path in documents:
        try:
            if path.suffix.lower() == ".pdf":
                validate_pdf(path)
            else:
                validate_pptx(path)
            print(f"OK {path.relative_to(root)}")
        except (OSError, ValueError, zipfile.BadZipFile) as error:
            failures.append(f"{path.relative_to(root)}: {error}")

    if failures:
        print("\nDocument validation failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print(f"Validated {len(documents)} document(s).")
    return 0


if __name__ == "__main__":
    repository_root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    raise SystemExit(validate_repository(repository_root))
