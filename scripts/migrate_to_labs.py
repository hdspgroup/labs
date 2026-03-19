from __future__ import annotations

import re
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
TARGET_EXTENSIONS = {".html", ".xml", ".json"}
TARGET_FILENAMES = {"site.webmanifest"}

ABSOLUTE_SITE_URL_PATTERN = re.compile(r"https://hdspgroup\.github\.io/(?!labs/)")
HTML_XML_ATTR_PATTERN = re.compile(
    r"(?P<attr>\b(?:href|src|content)\b)\s*=\s*(?P<quote>[\"'])(?P<value>.*?)(?P=quote)",
    re.IGNORECASE,
)
REL_PERMALINK_PATTERN = re.compile(r'("relpermalink"\s*:\s*")/(?!labs/)')
MANIFEST_START_URL_PATTERN = re.compile(r'("start_url"\s*:\s*")\./')
MANIFEST_SRC_PATTERN = re.compile(
    r'("src"\s*:\s*")(?!https?://|/labs/|data:)(?P<path>[^\"]+)'
)
META_REFRESH_ROOT_URL_PATTERN = re.compile(r"url=/(?!labs/)", re.IGNORECASE)


def iter_target_files(root_dir: Path) -> list[Path]:
    files: list[Path] = []
    for path in root_dir.rglob("*"):
        if not path.is_file():
            continue
        if ".git" in path.parts:
            continue
        if path.name in TARGET_FILENAMES or path.suffix.lower() in TARGET_EXTENSIONS:
            files.append(path)
    return files


def rewrite_html_xml_attr(match: re.Match[str]) -> str:
    attr = match.group("attr")
    quote = match.group("quote")
    value = match.group("value")

    value = ABSOLUTE_SITE_URL_PATTERN.sub("https://hdspgroup.github.io/labs/", value)

    if attr.lower() == "content":
        value = META_REFRESH_ROOT_URL_PATTERN.sub("url=/labs/", value)

    if value.startswith("/") and not value.startswith("//") and not value.startswith("/labs/"):
        value = f"/labs{value}"

    return f"{attr}={quote}{value}{quote}"


def rewrite_manifest_src(match: re.Match[str]) -> str:
    prefix = match.group(1)
    path = match.group("path")
    return f'{prefix}/labs/{path}'


def migrate_file(path: Path) -> bool:
    original_text = path.read_text(encoding="utf-8")
    updated_text = ABSOLUTE_SITE_URL_PATTERN.sub(
        "https://hdspgroup.github.io/labs/", original_text
    )

    suffix = path.suffix.lower()

    if suffix in {".html", ".xml"}:
        updated_text = HTML_XML_ATTR_PATTERN.sub(rewrite_html_xml_attr, updated_text)

    if suffix == ".json":
        updated_text = REL_PERMALINK_PATTERN.sub(r"\1/labs/", updated_text)

    if path.name == "site.webmanifest":
        updated_text = MANIFEST_START_URL_PATTERN.sub(r"\1/labs/", updated_text)
        updated_text = MANIFEST_SRC_PATTERN.sub(rewrite_manifest_src, updated_text)

    if updated_text == original_text:
        return False

    path.write_text(updated_text, encoding="utf-8")
    return True


def main() -> None:
    changed_files = 0
    target_files = iter_target_files(ROOT_DIR)

    for file_path in target_files:
        if migrate_file(file_path):
            changed_files += 1

    print(f"Updated {changed_files} files out of {len(target_files)} scanned.")


if __name__ == "__main__":
    main()