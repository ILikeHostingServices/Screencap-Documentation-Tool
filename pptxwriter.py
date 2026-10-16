#!/usr/bin/env python3
#
# pptxwriter.py
# 2026-10-16
# Version: v1.0.1
#
# PURPOSE:
# Writes a PowerPoint presentation (.pptx) of a recording's steps, with the
# Python standard library only (no PowerPoint, Pandoc, or python-pptx
# needed). A .pptx file is a zip of XML parts (Office Open XML); this
# module writes the parts PowerPoint needs and nothing else:
#
#   - a title slide: title, version, date, author, and the logo if one is set
#   - one 16:9 slide per step: "Step N", the screenshot as large as fits,
#     and the caption under it; the screenshot has its alt text, and spoken
#     narration (Captions From Narration) goes in the speaker notes
#   - a slide with the animated clip after a step that has one (it plays in
#     the slide show)
#
# Sizes are in EMU (English Metric Units): 914400 to the inch, 12700 to the
# point. Pictures are scaled to fit their box and keep their shape.

import re
import struct
import time
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

EMU_PER_INCH = 914400
SLIDE_W, SLIDE_H = 12192000, 6858000      # 13.333 x 7.5 in (16:9)
MARGIN = int(0.45 * EMU_PER_INCH)
TEXT = "1B1B1B"
MUTED = "666666"
ACCENT = "2563EB"
WARN = "C62828"
FONT = "Segoe UI"            # PowerPoint uses a similar font where it is missing

NS = ('xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
      'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"')
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
CT = "application/vnd.openxmlformats-officedocument.presentationml"
IMAGE_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
               ".gif": "image/gif"}
_BAD_XML = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f￾￿]")


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def x(text):
    """Text made safe for XML content and attributes."""
    return escape(_BAD_XML.sub("", str(text)), {'"': "&quot;"})


def image_size(path):
    """(width, height) in pixels of a PNG, GIF, or JPEG file."""
    data = Path(path).read_bytes()
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", data[16:24])
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return struct.unpack("<HH", data[6:10])
    if data[:2] == b"\xff\xd8":
        i = 2
        while i + 9 < len(data):
            if data[i] != 0xFF:
                i += 1
                continue
            marker = data[i + 1]
            if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
                i += 2
                continue
            length = struct.unpack(">H", data[i + 2:i + 4])[0]
            if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
                h, w = struct.unpack(">HH", data[i + 5:i + 9])
                return w, h
            i += 2 + length
    raise ValueError(f"{Path(path).name} is not a PNG, GIF, or JPEG picture")


def fit(img_w, img_h, box_w, box_h):
    """(width, height) of a picture scaled to fit the box, keeping its shape."""
    scale = min(box_w / img_w, box_h / img_h)
    return int(img_w * scale), int(img_h * scale)


def caption_size(text):
    """Caption font size in points: smaller for long captions."""
    n = len(text)
    return 20 if n <= 120 else 16 if n <= 260 else 13


# ---------------------------------------------------------------------------
# Shapes
# ---------------------------------------------------------------------------

def run(text, size, color=TEXT, bold=False):
    weight = ' b="1"' if bold else ""
    return (f'<a:r><a:rPr lang="en-US" sz="{size * 100}"{weight} '
            f'dirty="0"><a:solidFill><a:srgbClr val="{color}"/></a:solidFill>'
            f'<a:latin typeface="{FONT}"/><a:cs typeface="{FONT}"/></a:rPr>'
            f"<a:t>{x(text)}</a:t></a:r>")


def paragraphs(text, size, color=TEXT, bold=False, align="l"):
    """One paragraph per line of text."""
    lines = str(text).split("\n") or [""]
    out = []
    for line in lines:
        body = run(line, size, color, bold) if line else ""
        out.append(f'<a:p><a:pPr algn="{align}"/>{body}'
                   f'<a:endParaRPr lang="en-US" sz="{size * 100}" dirty="0"/></a:p>')
    return "".join(out)


def text_box(shape_id, name, left, top, width, height, body, anchor="t"):
    return (f'<p:sp><p:nvSpPr><p:cNvPr id="{shape_id}" name="{x(name)}"/>'
            f'<p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
            f'<p:spPr><a:xfrm><a:off x="{left}" y="{top}"/><a:ext cx="{width}" cy="{height}"/>'
            f'</a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/></p:spPr>'
            f'<p:txBody><a:bodyPr wrap="square" lIns="0" tIns="0" rIns="0" bIns="0" '
            f'anchor="{anchor}"><a:normAutofit/></a:bodyPr><a:lstStyle/>{body}</p:txBody></p:sp>')


def bar(shape_id, left, top, width, height, color):
    return (f'<p:sp><p:nvSpPr><p:cNvPr id="{shape_id}" name="Accent bar"/><p:cNvSpPr/>'
            f'<p:nvPr/></p:nvSpPr><p:spPr><a:xfrm><a:off x="{left}" y="{top}"/>'
            f'<a:ext cx="{width}" cy="{height}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/>'
            f'</a:prstGeom><a:solidFill><a:srgbClr val="{color}"/></a:solidFill>'
            f'<a:ln><a:noFill/></a:ln></p:spPr></p:sp>')


def picture(shape_id, name, rel_id, left, top, width, height, alt, border=True):
    line = ('<a:ln w="9525"><a:solidFill><a:srgbClr val="BFBFBF"/></a:solidFill></a:ln>'
            if border else "")
    return (f'<p:pic><p:nvPicPr><p:cNvPr id="{shape_id}" name="{x(name)}" descr="{x(alt)}"/>'
            f'<p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr><p:nvPr/></p:nvPicPr>'
            f'<p:blipFill><a:blip r:embed="{rel_id}"/><a:stretch><a:fillRect/></a:stretch>'
            f'</p:blipFill><p:spPr><a:xfrm><a:off x="{left}" y="{top}"/>'
            f'<a:ext cx="{width}" cy="{height}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/>'
            f'</a:prstGeom>{line}</p:spPr></p:pic>')


def slide_xml(shapes):
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<p:sld {NS}>'
            '<p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/>'
            '</p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/>'
            '<a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>'
            + "".join(shapes) +
            '</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>')


# ---------------------------------------------------------------------------
# The fixed parts: theme, master, layout, notes master
# ---------------------------------------------------------------------------

THEME = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    '<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Screencap">'
    '<a:themeElements><a:clrScheme name="Screencap">'
    '<a:dk1><a:sysClr val="windowText" lastClr="000000"/></a:dk1>'
    '<a:lt1><a:sysClr val="window" lastClr="FFFFFF"/></a:lt1>'
    '<a:dk2><a:srgbClr val="1B1B1B"/></a:dk2><a:lt2><a:srgbClr val="F2F2F2"/></a:lt2>'
    '<a:accent1><a:srgbClr val="2563EB"/></a:accent1><a:accent2><a:srgbClr val="E53935"/></a:accent2>'
    '<a:accent3><a:srgbClr val="43A047"/></a:accent3><a:accent4><a:srgbClr val="FB8C00"/></a:accent4>'
    '<a:accent5><a:srgbClr val="8E24AA"/></a:accent5><a:accent6><a:srgbClr val="00897B"/></a:accent6>'
    '<a:hlink><a:srgbClr val="2563EB"/></a:hlink><a:folHlink><a:srgbClr val="7B1FA2"/></a:folHlink>'
    '</a:clrScheme><a:fontScheme name="Screencap">'
    '<a:majorFont><a:latin typeface="Segoe UI"/><a:ea typeface=""/><a:cs typeface=""/></a:majorFont>'
    '<a:minorFont><a:latin typeface="Segoe UI"/><a:ea typeface=""/><a:cs typeface=""/></a:minorFont>'
    '</a:fontScheme><a:fmtScheme name="Screencap"><a:fillStyleLst>'
    '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
    '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
    '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:fillStyleLst><a:lnStyleLst>'
    '<a:ln w="6350"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln>'
    '<a:ln w="12700"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln>'
    '<a:ln w="19050"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln>'
    '</a:lnStyleLst><a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle>'
    '<a:effectStyle><a:effectLst/></a:effectStyle><a:effectStyle><a:effectLst/></a:effectStyle>'
    '</a:effectStyleLst><a:bgFillStyleLst>'
    '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
    '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
    '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst>'
    '</a:fmtScheme></a:themeElements><a:objectDefaults/><a:extraClrSchemeLst/></a:theme>')

EMPTY_TREE = ('<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
              '<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/>'
              '<a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>')
CLR_MAP = ('<p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" '
           'accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" '
           'accent6="accent6" hlink="hlink" folHlink="folHlink"/>')
LEVEL = '<a:lvl1pPr><a:defRPr sz="{sz}"><a:solidFill><a:schemeClr val="tx1"/></a:solidFill>' \
        '<a:latin typeface="+mn-lt"/></a:defRPr></a:lvl1pPr>'

MASTER = (
    f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<p:sldMaster {NS}>'
    '<p:cSld><p:bg><p:bgPr><a:solidFill><a:srgbClr val="FFFFFF"/></a:solidFill>'
    f'<a:effectLst/></p:bgPr></p:bg><p:spTree>{EMPTY_TREE}</p:spTree></p:cSld>{CLR_MAP}'
    '<p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst>'
    f'<p:txStyles><p:titleStyle>{LEVEL.format(sz=4000)}</p:titleStyle>'
    f'<p:bodyStyle>{LEVEL.format(sz=2000)}</p:bodyStyle>'
    f'<p:otherStyle>{LEVEL.format(sz=1800)}</p:otherStyle></p:txStyles></p:sldMaster>')

LAYOUT = (
    f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    f'<p:sldLayout {NS} type="blank" preserve="1"><p:cSld name="Blank">'
    f'<p:spTree>{EMPTY_TREE}</p:spTree></p:cSld>'
    '<p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sldLayout>')


def _placeholder(shape_id, name, kind, idx, left, top, width, height, text_body=""):
    idx_attr = f' idx="{idx}"' if idx is not None else ""
    empty = '<a:p><a:endParaRPr lang="en-US"/></a:p>'
    body = (f'<p:txBody><a:bodyPr/><a:lstStyle/>{text_body or empty}</p:txBody>'
            if kind == "body" else "")
    lock = '<a:spLocks noGrp="1" noRot="1" noChangeAspect="1"/>' if kind == "sldImg" \
        else '<a:spLocks noGrp="1"/>'
    return (f'<p:sp><p:nvSpPr><p:cNvPr id="{shape_id}" name="{name}"/><p:cNvSpPr>{lock}'
            f'</p:cNvSpPr><p:nvPr><p:ph type="{kind}"{idx_attr}/></p:nvPr></p:nvSpPr>'
            f'<p:spPr><a:xfrm><a:off x="{left}" y="{top}"/><a:ext cx="{width}" cy="{height}"/>'
            f'</a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr>{body}</p:sp>')


NOTES_W, NOTES_H = 6858000, 9144000
NOTES_IMG = (685800, 1143000, 5486400, 3086100)
NOTES_BODY = (685800, 4400550, 5486400, 3600450)

NOTES_MASTER = (
    f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<p:notesMaster {NS}>'
    '<p:cSld><p:bg><p:bgRef idx="1001"><a:schemeClr val="bg1"/></p:bgRef></p:bg>'
    f'<p:spTree>{EMPTY_TREE}'
    + _placeholder(2, "Slide Image Placeholder 1", "sldImg", 2, *NOTES_IMG)
    + _placeholder(3, "Notes Placeholder 2", "body", 3, *NOTES_BODY)
    + f'</p:spTree></p:cSld>{CLR_MAP}'
    f'<p:notesStyle>{LEVEL.format(sz=1200)}</p:notesStyle></p:notesMaster>')


def notes_xml(text):
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<p:notes {NS}>'
            f'<p:cSld><p:spTree>{EMPTY_TREE}'
            + _placeholder(2, "Slide Image Placeholder 1", "sldImg", None, *NOTES_IMG)
            + _placeholder(3, "Notes Placeholder 2", "body", 1, *NOTES_BODY,
                           text_body=paragraphs(text, 12))
            + '</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:notes>')


def rels(items):
    """Relationships part: items are (id, type suffix, target)."""
    body = "".join(f'<Relationship Id="{rid}" Type="{R}/{kind}" Target="{x(target)}"/>'
                   for rid, kind, target in items)
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            f'<Relationships xmlns="{REL_NS}">{body}</Relationships>')


# ---------------------------------------------------------------------------
# The presentation
# ---------------------------------------------------------------------------

class Deck:
    """Collects slides, then writes the .pptx package."""

    def __init__(self):
        self.slides = []      # (slide xml, [(rel id, media name)], notes text or None)
        self.media = {}       # media name -> source path
        self._media_keys = {}

    def add_media(self, path):
        """Name of the picture inside the package (each file is stored once)."""
        path = Path(path)
        key = str(path.resolve())
        if key not in self._media_keys:
            ext = path.suffix.lower()
            if ext == ".jpeg":
                ext = ".jpg"
            name = f"image{len(self.media) + 1}{ext}"
            self.media[name] = path
            self._media_keys[key] = name
        return self._media_keys[key]

    def add_slide(self, shapes, pictures=(), notes=None):
        """pictures: media names in the order of their r:embed ids rId2, rId3..."""
        self.slides.append((slide_xml(shapes), list(pictures), notes))

    def write(self, dest, title="", author=""):
        dest = Path(dest)
        has_notes = any(n for _, _, n in self.slides)
        tmp = dest.with_name(dest.name + ".tmp")
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("[Content_Types].xml", self._content_types(has_notes))
            z.writestr("_rels/.rels", (
                f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
                f'<Relationships xmlns="{REL_NS}">'
                f'<Relationship Id="rId1" Type="{R}/officeDocument" Target="ppt/presentation.xml"/>'
                '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/'
                'relationships/metadata/core-properties" Target="docProps/core.xml"/>'
                f'<Relationship Id="rId3" Type="{R}/extended-properties" Target="docProps/app.xml"/>'
                '</Relationships>'))
            z.writestr("docProps/core.xml", self._core(title, author))
            z.writestr("docProps/app.xml", (
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
                '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/'
                'extended-properties"><Application>ScreenCap Docs</Application>'
                f'<PresentationFormat>Widescreen</PresentationFormat><Slides>{len(self.slides)}'
                '</Slides></Properties>'))
            z.writestr("ppt/presentation.xml", self._presentation(has_notes))
            items = [("rId1", "slideMaster", "slideMasters/slideMaster1.xml")]
            items += [(f"rId{i + 2}", "slide", f"slides/slide{i + 1}.xml")
                      for i in range(len(self.slides))]
            n = len(self.slides) + 2
            items += [(f"rId{n}", "theme", "theme/theme1.xml"),
                      (f"rId{n + 1}", "presProps", "presProps.xml"),
                      (f"rId{n + 2}", "viewProps", "viewProps.xml"),
                      (f"rId{n + 3}", "tableStyles", "tableStyles.xml")]
            if has_notes:
                items.append((f"rId{n + 4}", "notesMaster", "notesMasters/notesMaster1.xml"))
            z.writestr("ppt/_rels/presentation.xml.rels", rels(items))
            z.writestr("ppt/presProps.xml",
                       f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
                       f'<p:presentationPr {NS}/>')
            z.writestr("ppt/viewProps.xml", (
                f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<p:viewPr {NS}>'
                '<p:normalViewPr><p:restoredLeft sz="15620"/><p:restoredTop sz="94660"/>'
                '</p:normalViewPr><p:gridSpacing cx="76200" cy="76200"/></p:viewPr>'))
            z.writestr("ppt/tableStyles.xml", (
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
                '<a:tblStyleLst xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
                'def="{5C22544A-7EE6-4342-B048-85BDC9FD1C3A}"/>'))
            z.writestr("ppt/theme/theme1.xml", THEME)
            z.writestr("ppt/slideMasters/slideMaster1.xml", MASTER)
            z.writestr("ppt/slideMasters/_rels/slideMaster1.xml.rels", rels([
                ("rId1", "slideLayout", "../slideLayouts/slideLayout1.xml"),
                ("rId2", "theme", "../theme/theme1.xml")]))
            z.writestr("ppt/slideLayouts/slideLayout1.xml", LAYOUT)
            z.writestr("ppt/slideLayouts/_rels/slideLayout1.xml.rels", rels([
                ("rId1", "slideMaster", "../slideMasters/slideMaster1.xml")]))
            if has_notes:
                z.writestr("ppt/theme/theme2.xml", THEME)
                z.writestr("ppt/notesMasters/notesMaster1.xml", NOTES_MASTER)
                z.writestr("ppt/notesMasters/_rels/notesMaster1.xml.rels", rels([
                    ("rId1", "theme", "../theme/theme2.xml")]))
            notes_n = 0
            for i, (xml, pictures, notes) in enumerate(self.slides, 1):
                z.writestr(f"ppt/slides/slide{i}.xml", xml)
                items = [("rId1", "slideLayout", "../slideLayouts/slideLayout1.xml")]
                items += [(f"rId{k + 2}", "image", f"../media/{name}")
                          for k, name in enumerate(pictures)]
                if notes:
                    notes_n += 1
                    items.append((f"rId{len(pictures) + 2}", "notesSlide",
                                  f"../notesSlides/notesSlide{notes_n}.xml"))
                    z.writestr(f"ppt/notesSlides/notesSlide{notes_n}.xml", notes_xml(notes))
                    z.writestr(f"ppt/notesSlides/_rels/notesSlide{notes_n}.xml.rels", rels([
                        ("rId1", "notesMaster", "../notesMasters/notesMaster1.xml"),
                        ("rId2", "slide", f"../slides/slide{i}.xml")]))
                z.writestr(f"ppt/slides/_rels/slide{i}.xml.rels", rels(items))
            for name, path in self.media.items():
                z.write(path, f"ppt/media/{name}")
        tmp.replace(dest)
        return dest

    def _content_types(self, has_notes):
        exts = {Path(n).suffix.lower() for n in self.media}
        defaults = ['<Default Extension="rels" ContentType="application/'
                    'vnd.openxmlformats-package.relationships+xml"/>',
                    '<Default Extension="xml" ContentType="application/xml"/>']
        defaults += [f'<Default Extension="{e[1:]}" ContentType="{IMAGE_TYPES[e]}"/>'
                     for e in sorted(exts)]
        parts = [("/ppt/presentation.xml", f"{CT}.presentation.main+xml"),
                 ("/ppt/slideMasters/slideMaster1.xml", f"{CT}.slideMaster+xml"),
                 ("/ppt/slideLayouts/slideLayout1.xml", f"{CT}.slideLayout+xml"),
                 ("/ppt/theme/theme1.xml", "application/vnd.openxmlformats-officedocument.theme+xml"),
                 ("/ppt/presProps.xml", f"{CT}.presProps+xml"),
                 ("/ppt/viewProps.xml", f"{CT}.viewProps+xml"),
                 ("/ppt/tableStyles.xml", f"{CT}.tableStyles+xml"),
                 ("/docProps/core.xml", "application/vnd.openxmlformats-package.core-properties+xml"),
                 ("/docProps/app.xml",
                  "application/vnd.openxmlformats-officedocument.extended-properties+xml")]
        parts += [(f"/ppt/slides/slide{i}.xml", f"{CT}.slide+xml")
                  for i in range(1, len(self.slides) + 1)]
        if has_notes:
            parts += [("/ppt/theme/theme2.xml",
                       "application/vnd.openxmlformats-officedocument.theme+xml"),
                      ("/ppt/notesMasters/notesMaster1.xml", f"{CT}.notesMaster+xml")]
            count = sum(1 for _, _, n in self.slides if n)
            parts += [(f"/ppt/notesSlides/notesSlide{i}.xml", f"{CT}.notesSlide+xml")
                      for i in range(1, count + 1)]
        overrides = "".join(f'<Override PartName="{p}" ContentType="{c}"/>' for p, c in parts)
        return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
                '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                + "".join(defaults) + overrides + "</Types>")

    def _presentation(self, has_notes):
        n = len(self.slides) + 2
        notes = (f'<p:notesMasterIdLst><p:notesMasterId r:id="rId{n + 4}"/></p:notesMasterIdLst>'
                 if has_notes else "")
        ids = "".join(f'<p:sldId id="{256 + i}" r:id="rId{i + 2}"/>'
                      for i in range(len(self.slides)))
        return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
                f'<p:presentation {NS} saveSubsetFonts="1">'
                '<p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst>'
                f'{notes}<p:sldIdLst>{ids}</p:sldIdLst>'
                f'<p:sldSz cx="{SLIDE_W}" cy="{SLIDE_H}"/>'
                f'<p:notesSz cx="{NOTES_W}" cy="{NOTES_H}"/></p:presentation>')

    @staticmethod
    def _core(title, author):
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
                '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/'
                'metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" '
                'xmlns:dcterms="http://purl.org/dc/terms/" '
                'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
                f"<dc:title>{x(title)}</dc:title><dc:creator>{x(author)}</dc:creator>"
                f'<dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created>'
                f'<dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified>'
                "</cp:coreProperties>")


# ---------------------------------------------------------------------------
# Slides for a recording's steps
# ---------------------------------------------------------------------------

def title_slide(deck, meta, logo=None, warning=None):
    shapes, pics = [], []
    top = int(2.3 * EMU_PER_INCH)
    if logo is not None:
        lw, lh = fit(*image_size(logo), int(3.2 * EMU_PER_INCH), int(1.1 * EMU_PER_INCH))
        pics.append(deck.add_media(logo))
        shapes.append(picture(len(shapes) + 2, "Logo", "rId2", MARGIN + int(0.3 * EMU_PER_INCH),
                              int(0.7 * EMU_PER_INCH), lw, lh, "Logo", border=False))
    left = MARGIN + int(0.3 * EMU_PER_INCH)
    width = SLIDE_W - 2 * left
    shapes.append(bar(len(shapes) + 2, left, top - int(0.25 * EMU_PER_INCH),
                      int(1.2 * EMU_PER_INCH), int(0.08 * EMU_PER_INCH), ACCENT))
    shapes.append(text_box(len(shapes) + 2, "Title", left, top, width,
                           int(1.6 * EMU_PER_INCH), paragraphs(meta["title"], 40, bold=True),
                           anchor="t"))
    line = f'Version {meta["version"]}  ·  {meta["date"]}'
    if meta.get("author"):
        line += f'  ·  {meta["author"]}'
    shapes.append(text_box(len(shapes) + 2, "Details", left, top + int(1.75 * EMU_PER_INCH),
                           width, int(0.6 * EMU_PER_INCH), paragraphs(line, 20, MUTED)))
    if warning:
        shapes.append(text_box(len(shapes) + 2, "Warning", left, top + int(2.6 * EMU_PER_INCH),
                               width, int(1.0 * EMU_PER_INCH),
                               paragraphs(warning, 18, WARN, bold=True)))
    deck.add_slide(shapes, pics)


def step_slide(deck, number, timestamp, image, alt, caption, notes=None, logo=None,
               heading=None):
    shapes, pics = [], []
    head_h = int(0.62 * EMU_PER_INCH)
    heading = heading or f"Step {number}"
    body = run(heading, 26, bold=True) + run(f"   {timestamp}", 14, MUTED) if timestamp \
        else run(heading, 26, bold=True)
    shapes.append(text_box(2, "Step", MARGIN, int(0.3 * EMU_PER_INCH),
                           SLIDE_W - 2 * MARGIN - int(2.0 * EMU_PER_INCH), head_h,
                           f'<a:p><a:pPr algn="l"/>{body}</a:p>', anchor="ctr"))
    if logo is not None:
        lw, lh = fit(*image_size(logo), int(1.8 * EMU_PER_INCH), int(0.5 * EMU_PER_INCH))
        pics.append(deck.add_media(logo))
        shapes.append(picture(3, "Logo", f"rId{len(pics) + 1}", SLIDE_W - MARGIN - lw,
                              int(0.3 * EMU_PER_INCH) + (head_h - lh) // 2, lw, lh, "Logo",
                              border=False))
    caption = (caption or "").strip()
    cap_h = 0
    if caption:
        lines = caption.count("\n") + 1 + len(caption) // 110
        cap_h = int(min(1.6, 0.35 + 0.34 * lines) * EMU_PER_INCH)
    box_top = int(0.3 * EMU_PER_INCH) + head_h + int(0.18 * EMU_PER_INCH)
    box_bottom = SLIDE_H - int(0.35 * EMU_PER_INCH) - (cap_h + int(0.15 * EMU_PER_INCH)
                                                         if caption else 0)
    box_w = SLIDE_W - 2 * MARGIN
    pw, ph = fit(*image_size(image), box_w, box_bottom - box_top)
    pics.append(deck.add_media(image))
    shapes.append(picture(len(shapes) + 2, "Screenshot", f"rId{len(pics) + 1}",
                          (SLIDE_W - pw) // 2, box_top, pw, ph, alt))
    if caption:
        shapes.append(text_box(len(shapes) + 2, "Caption", MARGIN,
                               box_top + ph + int(0.15 * EMU_PER_INCH), box_w, cap_h,
                               paragraphs(caption, caption_size(caption))))
    deck.add_slide(shapes, pics, notes)
