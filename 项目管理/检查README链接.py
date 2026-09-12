from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
VENDOR_PREFIX = ("论文", "cumcm-paper-agent-skills")
LINK_PATTERN = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")


def main() -> int:
    checked = 0
    missing: list[str] = []
    readmes = sorted(ROOT.rglob("README.md"))
    for readme in readmes:
        relative_parts = readme.relative_to(ROOT).parts
        if relative_parts[: len(VENDOR_PREFIX)] == VENDOR_PREFIX:
            continue
        text = readme.read_text(encoding="utf-8-sig")
        for raw_target in LINK_PATTERN.findall(text):
            target = raw_target.strip().strip("<>")
            if not target or target.startswith(("#", "http://", "https://", "mailto:")):
                continue
            path_text = unquote(target.split("#", 1)[0])
            resolved = (readme.parent / path_text).resolve()
            checked += 1
            if not resolved.exists():
                missing.append(f"{readme.relative_to(ROOT).as_posix()} -> {target}")

    print(f"owned_readmes={sum(1 for p in readmes if p.relative_to(ROOT).parts[:len(VENDOR_PREFIX)] != VENDOR_PREFIX)}")
    print(f"relative_links_checked={checked}")
    if missing:
        print("missing_links:")
        for item in missing:
            print(f"- {item}")
        return 1
    print("missing_links=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
