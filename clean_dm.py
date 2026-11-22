#!/usr/bin/env python3
"""Re-host davidmuma's EPG with a fix IPTVBoss needs.

davidmuma's guide emits some <rating>/<star-rating> elements with no `system`
attribute. IPTVBoss's EPG writer assumes every rating has one and throws a
NullPointerException (EpgWriter.writeXMLElement) on the first that doesn't,
aborting the whole EPG write. This script adds system="other" to any such tag,
validates the result, and writes a cleaned .xml.gz for IPTVBoss to read.

Add more davidmuma files to SOURCES if you ever load others.
"""
import gzip, re, sys, urllib.request
import xml.etree.ElementTree as ET

SOURCES = {
    # output filename in this repo : source URL
    "guiatv_sincolor1.xml.gz":
        "https://raw.githubusercontent.com/davidmuma/EPG_dobleM/master/guiatv_sincolor1.xml.gz",
}

# any <rating ...> or <star-rating ...> opening tag that lacks a system= attr
MISSING = re.compile(rb'<(rating|star-rating)(?![^>]*\bsystem=)([^>]*)>')

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=180) as r:
        raw = r.read()
    try:
        return gzip.decompress(raw)        # source is gzipped
    except OSError:
        return raw                         # already plain xml

def main():
    rc = 0
    for out, url in SOURCES.items():
        try:
            xml = fetch(url)
        except Exception as e:
            print(f"{out}: FETCH FAILED ({e}) - keeping existing file"); rc = 1; continue
        before = len(MISSING.findall(xml))
        fixed = MISSING.sub(rb'<\1 system="other"\2>', xml)
        try:
            ET.fromstring(fixed)           # don't publish if we broke it
        except ET.ParseError as e:
            print(f"{out}: FIXED FILE NOT WELL-FORMED ({e}) - keeping existing file"); rc = 1; continue
        with open(out, "wb") as f:         # mtime=0 -> identical input = identical bytes (no noise commits)
            with gzip.GzipFile(fileobj=f, mode="wb", mtime=0) as g:
                g.write(fixed)
        print(f"{out}: fixed {before} system-less rating(s), wrote {len(fixed)} bytes xml")
    sys.exit(rc)

if __name__ == "__main__":
    main()
