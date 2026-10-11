"""Check that version numbers agree across the repo, and write release notes.

    python scripts/check_release.py              # consistency check (CI)
    python scripts/check_release.py v1.2.0       # also check a tag, write notes to release-notes.md
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def fail(msg: str) -> None:
    sys.exit(f"check_release: {msg}")


def main() -> None:
    server = json.loads((ROOT / "server.json").read_text())["version"]
    changelog = (ROOT / "CHANGELOG.md").read_text()
    released = re.findall(r"^## \[(\d+\.\d+\.\d+)\]", changelog, re.M)
    if not released:
        fail("CHANGELOG.md has no released version headings")
    if released[0] != server:
        fail(f"server.json is {server} but the latest CHANGELOG release is {released[0]}")

    citation = re.search(r"^version: (\S+)", (ROOT / "CITATION.cff").read_text(), re.M).group(1)
    if citation != server:
        fail(f"CITATION.cff is {citation} but server.json is {server}")

    footprint = (ROOT / "server" / "footprint.py").read_text()
    methodology = re.search(r'^METHODOLOGY_VERSION = "([^"]+)"', footprint, re.M).group(1)
    readme = (ROOT / "README.md").read_text()
    if f"methodology-{methodology.replace('-', '--')}" not in readme:
        fail(f"README methodology badge doesn't show {methodology}")
    for banner in (ROOT / "docs" / "assets").glob("banner-*.svg"):
        if f"methodology {methodology}" not in banner.read_text():
            fail(f"{banner.name} doesn't show methodology {methodology}")

    if len(sys.argv) > 1:
        tag = sys.argv[1]
        if tag != f"v{server}":
            fail(f"tag {tag} doesn't match server.json version v{server}")
        section = re.search(rf"^## \[{re.escape(server)}\][^\n]*\n(.*?)(?=^## \[|^\[[^\]]+\]: )", changelog, re.M | re.S)
        notes = section.group(1).strip()
        notes += f"\n\n**Methodology:** `{methodology}` · **Full changelog:** [CHANGELOG.md](https://github.com/nickjlamb/ai-footprint/blob/main/CHANGELOG.md)"
        (ROOT / "release-notes.md").write_text(notes + "\n")

    print(f"ok: version {server}, methodology {methodology}")


if __name__ == "__main__":
    main()
