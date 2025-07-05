from pathlib import Path
import mimetypes
import sys

TEXT_EXTS = {".py", ".js", ".jsx", ".ts", ".tsx",
             ".json", ".md", ".css", ".html", ".txt", ".yml", ".yaml"}

def dump_project_sources(
    root: Path | str = ".",
    out_file: Path | str = "project_sources.txt",
    skip_dirs: tuple[str, ...] = (".git", ".venv", "node_modules", "__pycache__", ".pytest_cache", "data", "requirements.txt", "public", "assets"),
    text_mimetypes: tuple[str, ...] = ("text/", "application/json", "application/javascript")
) -> None:
    """
    Recursively walks *root* and writes every (probable) text-file's contents to *out_file*.

    • Each file is preceded by a banner line with its **path relative to project root**,
      e.g.  ==== backend/app/main.py ====
    • Binary files (detected with mimetypes) are skipped.
    • Directories in *skip_dirs* are not descended into.

    Parameters
    ----------
    root : Path | str
        Project root; default is current working directory.
    out_file : Path | str
        Where to write the concatenated output.
    skip_dirs : tuple[str, ...]
        Directory names to ignore entirely.
    text_mimetypes : tuple[str, ...]
        Mimetype prefixes considered “text”. Adjust if needed.
    """
    root = Path(root).resolve()
    out_path = Path(out_file).resolve()

    with out_path.open("w", encoding="utf-8") as bundle:
        for path in sorted(root.rglob("*")):
            # Skip directories we don't want to descend into
            if any(part in skip_dirs for part in path.relative_to(root).parts):
                continue
            if path.is_file():
                ext_ok = path.suffix.lower() in TEXT_EXTS
                mtype, _ = mimetypes.guess_type(path.name)
                # Very light heuristic: skip files that look binary
                if not ext_ok and (mtype is None or not mtype.startswith(text_mimetypes)):
                    print(f"Skipped (binary?): {path.relative_to(root)}", file=sys.stderr)
                    continue

                rel = path.relative_to(root)
                banner = f"\n==== {rel.as_posix()} ====\n"
                bundle.write(banner)

                try:
                    bundle.write(path.read_text(encoding="utf-8"))
                except UnicodeDecodeError:
                    # fall back to Latin-1, or skip if still unreadable
                    try:
                        bundle.write(path.read_text(encoding="latin-1"))
                    except Exception:
                        print(f"Skipped (binary?): {rel}", file=sys.stderr)

    print(f"★ Done. Wrote concatenated sources to {out_path}")

# --------------------------------------------------------------------
if __name__ == "__main__":
    dump_project_sources(root="landing", out_file="landing_src.txt")
# --------------------------------------------------------------------