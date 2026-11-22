#!/usr/bin/env python3
"""Re-host davidmuma's EPG with the fix IPTVBoss needs.

~Nov 2026 davidmuma's guide started carrying <rating>/<star-rating> blocks.
IPTVBoss's custom-EPG parser (EpgElementParserCustom.writeXMLElement) throws a
NullPointerException on them, which aborts the entire EPG write. This script
strips those blocks out (IPTVBoss doesn't use ratings for the guide) and dedups
duplicate channel ids, then validates and writes a cleaned .xml.gz.

Add more davidmuma files to SOURCES if you load others.
"""
import gzip, re, sys, urllib.request
import xml.etree.ElementTree as ET

SOURCES = {
    # output filename in this repo : source URL
    "guiatv_sincolor1.xml.gz":
        "https://raw.githubusercontent.com/davidmuma/EPG_dobleM/master/guiatv_sincolor1.xml.gz",
}

RATING   = re.compile(rb'<rating\b[^>]*>.*?</rating>', re.S)
STAR     = re.compile(rb'<star-rating\b[^>]*>.*?</star-rating>', re.S)
CHANNEL  = re.compile(rb'<channel id="([^"]*)">.*?</channel>', re.S)

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=180) as r:
        raw = r.read()
    try:
        return gzip.decompress(raw)
    except OSError:
        return raw

def clean(data):
    r = len(RATING.findall(data)); s = len(STAR.findall(data))
    data = RATING.sub(b'', data)
    data = STAR.sub(b'', data)
    seen = set()
    def dedup(m):
        cid = m.group(1)
        if cid in seen:
            return b''
        seen.add(cid); return m.group(0)
    dups_before = len(CHANNEL.findall(data))
    data = CHANNEL.sub(dedup, data)
    return data, r, s, dups_before - len(seen)

def main():
    rc = 0
    for out, url in SOURCES.items():
        try:
            xml = fetch(url)
        except Exception as e:
            print(f"{out}: FETCH FAILED ({e}) - keeping existing file"); rc = 1; continue
        fixed, nr, ns, nd = clean(xml)
        try:
            ET.fromstring(fixed)
        except ET.ParseError as e:
            print(f"{out}: cleaned file NOT well-formed ({e}) - keeping existing file"); rc = 1; continue
        with open(out, "wb") as f:
            with gzip.GzipFile(fileobj=f, mode="wb", mtime=0) as g:
                g.write(fixed)
        print(f"{out}: removed {nr} rating + {ns} star-rating block(s), deduped {nd} channel(s)")
    sys.exit(rc)

if __name__ == "__main__":
    main()
