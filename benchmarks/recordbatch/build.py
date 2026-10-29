"""Build the dependency-free, archive-only RecordBatch command."""

import shutil
import tempfile
import zipapp
from pathlib import Path


def main() -> None:
    """Package only the public application module and entrypoint."""
    root = Path(__file__).resolve().parent
    with tempfile.TemporaryDirectory() as directory:
        target = Path(directory)
        shutil.copy2(root / "recordbatch.py", target / "recordbatch.py")
        (target / "__main__.py").write_text("from recordbatch import main\nmain()\n")
        zipapp.create_archive(target, root / "recordbatch.pyz", interpreter="/usr/bin/env python3")


if __name__ == "__main__":
    main()
