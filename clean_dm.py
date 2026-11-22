#!/usr/bin/env python3
"""Re-host davidmuma's dobleM EPG for IPTVBoss.

Keeps the FULL guide (all channels, descriptions, ratings, icons, categories).
Only removes corrupted characters davidmuma's feed sometimes carries -
invisible control codes (U+0000-U+001F except tab/newline, U+007F-U+009F),
U+FFFD replacement marks, zero-width spaces, soft hyphens and BOMs - which
crash IPTVBoss's EPG writer (NullPointerException in EpgWriter.writeXMLElement).
Also dedups duplicate channel ids. Validates before writing; on any failure the
previous file is kept.

Add more davidmuma files to SOURCES if you load others.
"""
import gzip, re, sys, urllib.request
import xml.etree.ElementTree as ET

SOURCES = {
    "guiatv_sincolor1.xml.gz":
        "https://raw.githubusercontent.com/davidmuma/EPG_dobleM/master/guiatv_sincolor1.xml.gz",
}

BAD_CHARS = re.compile('[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f�​­﻿]')
CHANNEL   = re.compile(r'<channel id="([^"]*)">.*?</channel>\s*', re.S)

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=180) as r:
        raw = r.read()
    try:
        raw = gzip.decompress(raw)
    except OSError:
        pass
    return raw.decode("utf-8", errors="replace")

def clean(text):
    nbad = len(BAD_CHARS.findall(text))
    text = BAD_CHARS.sub('', text)
    seen = set(); ndup = 0
    def dedup(m):
        nonlocal ndup
        if m.group(1) in seen:
            ndup += 1; return ''
        seen.add(m.group(1)); return m.group(0)
    text = CHANNEL.sub(dedup, text)
    return text, nbad, ndup

def main():
    rc = 0
    for out, url in SOURCES.items():
        try:
            xml = fetch(url)
        except Exception as e:
            print(f"{out}: FETCH FAILED ({e}) - keeping existing file"); rc = 1; continue
        fixed, nbad, ndup = clean(xml)
        try:
            ET.fromstring(fixed.encode("utf-8"))
        except ET.ParseError as e:
            print(f"{out}: cleaned file NOT well-formed ({e}) - keeping existing file"); rc = 1; continue
        with open(out, "wb") as f:
            with gzip.GzipFile(fileobj=f, mode="wb", mtime=0) as g:
                g.write(fixed.encode("utf-8"))
        print(f"{out}: removed {nbad} corrupt char(s), deduped {ndup} channel(s)")
    sys.exit(rc)

if __name__ == "__main__":
    main()
