#!/usr/bin/env python3
#
# make_version_info.py
# 2026-10-04
# Version: v1.0.0
#
# PURPOSE:
# Writes the Windows version resource (the details on a file's Properties >
# Details tab) for the packaged .exe files, from version.py, so every build
# shows the right product name, version, and publisher. Used by
# screencap.spec; run from the repository root:
#   python packaging/make_version_info.py build/version_info.txt

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import version  # noqa: E402

TEMPLATE = """VSVersionInfo(
  ffi=FixedFileInfo(filevers={nums}, prodvers={nums}, mask=0x3f, flags=0x0,
                    OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)),
  kids=[
    StringFileInfo([StringTable('040904B0', [
      StringStruct('CompanyName', 'ILikeHostingServices'),
      StringStruct('FileDescription', '{app}'),
      StringStruct('FileVersion', '{ver}'),
      StringStruct('InternalName', 'ScreencapDocumentationTool'),
      StringStruct('LegalCopyright', 'Copyright (c) 2026 ILikeHostingServices. MIT License.'),
      StringStruct('OriginalFilename', 'Screencap Documentation Tool.exe'),
      StringStruct('ProductName', '{app}'),
      StringStruct('ProductVersion', '{ver}')])]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""


def main(argv):
    out = Path(argv[1]) if len(argv) > 1 else ROOT / "build" / "version_info.txt"
    major, minor, patch = (int(x) for x in version.RELEASE.split("."))
    text = TEMPLATE.format(nums=(major, minor, patch, 0), ver=version.RELEASE,
                           app=version.APP_NAME)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(f"Wrote {out} for v{version.RELEASE}")


if __name__ == "__main__":
    main(sys.argv)
