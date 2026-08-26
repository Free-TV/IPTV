#!/usr/bin/python3
"""Report which channels in `lists/` are no longer reachable.

The playlist checker records the URLs it could not open, but a bare URL does not say
which channel or which list it came from, and one failed attempt does not mean a
channel is gone. Streams time out, rate limit, move between CDNs, and some are only
served inside their own country.

This script maps every URL back to its channel and list, probes each one several
times, and separates the cases that look alike from the outside:

  dead         every attempt said "not found", so the stream is really gone
  blocked      the server answered but refused us, which is what a channel served
               only in its own country looks like from anywhere else
  unreachable  every attempt timed out or failed to connect
  flaky        answered at least once, so it is up but unreliable from here
  alive        answered every time

Only `dead` is safe to act on without a second opinion. `blocked` in particular must
not be treated as a fault: the lists mark geo-blocked channels deliberately.

Both playlist formats used by the lists are understood, HLS (.m3u8) and MPEG-DASH
(.mpd), so a DASH stream is not mistaken for a broken one.

Usage:
    ./check_channels.py                      # every list
    ./check_channels.py greece italy         # only those lists
    ./check_channels.py --attempts 5 greece  # more attempts per channel
"""

import argparse
import os
import re
import ssl
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

LISTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lists")

# `| 1 | Channel name | [>](url) | ...` is the row format used by every list
ROW = re.compile(r"^\|[^|]*\|([^|]+)\|[^|]*\[>\]\((https?://[^)\s]+)\)")

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0 Safari/537.36"
)

OK = "ok"
GONE = "gone"
REFUSED = "refused"
UNREACHABLE = "unreachable"

ALIVE = "alive"
DEAD = "dead"
BLOCKED = "blocked"
UNREACHED = "unreachable"
FLAKY = "flaky"

# a channel served only in its own country answers, then refuses us
REFUSING_CODES = (401, 402, 403, 451)
GONE_CODES = (404, 410)


def read_channels(name):
    """Return the `(channel, url)` pairs of the list called `name`."""
    path = os.path.join(LISTS_DIR, name + ".md")
    channels = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            match = ROW.match(line.strip())
            if match:
                channels.append((match.group(1).strip(), match.group(2)))
    return channels


def looks_like_a_playlist(head):
    """Return True if `head` is the start of an HLS or a DASH playlist."""
    text = head.lstrip()
    if text.startswith("#EXTM3U"):
        return True
    # DASH manifests are XML, and may carry a declaration, a comment or neither
    return "<MPD" in text[:2000]


def probe(url, timeout):
    """Open `url` once and report what the server did."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    # a stream whose certificate does not verify is still a working stream
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    try:
        with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
            head = response.read(3000).decode("utf-8", "ignore")
    except urllib.error.HTTPError as error:
        if error.code in GONE_CODES:
            return GONE
        if error.code in REFUSING_CODES:
            return REFUSED
        return UNREACHABLE
    except (urllib.error.URLError, OSError, ValueError):
        return UNREACHABLE
    return OK if looks_like_a_playlist(head) else GONE


def classify(outcomes):
    """Turn the outcomes of the attempts on one channel into a single state."""
    if all(outcome == OK for outcome in outcomes):
        return ALIVE
    if any(outcome == OK for outcome in outcomes):
        return FLAKY
    if any(outcome == REFUSED for outcome in outcomes):
        return BLOCKED
    if all(outcome == GONE for outcome in outcomes):
        return DEAD
    return UNREACHED


def check(channel, attempts, timeout, pause):
    """Probe one channel `attempts` times and return its state."""
    name, url = channel
    outcomes = []
    for attempt in range(attempts):
        outcomes.append(probe(url, timeout))
        if attempt + 1 < attempts:
            time.sleep(pause)
    return name, url, classify(outcomes), outcomes


def check_list(name, attempts, timeout, pause, workers):
    """Probe every channel of one list and return the results."""
    channels = [c for c in read_channels(name) if not c[1].startswith("https://www.youtube.com")]

    def run(channel):
        return check(channel, attempts, timeout, pause)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(run, channels))


def report(name, results, attempts):
    """Print the results of one list and return how many channels are dead."""
    states = {}
    for _, _, state, _ in results:
        states[state] = states.get(state, 0) + 1
    summary = ", ".join(f"{states[s]} {s}" for s in sorted(states))
    print(f"{name}: {len(results)} checked, {summary}")
    for channel, url, state, outcomes in results:
        if state == ALIVE:
            continue
        detail = "/".join(outcomes) if state != FLAKY else f"{outcomes.count(OK)}/{attempts} ok"
        print(f"  {state:12} {channel} [{detail}] -> {url}")
    return states.get(DEAD, 0)


def main():
    """Check the lists named on the command line, or every list."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("lists", nargs="*", help="lists to check, without the .md suffix")
    parser.add_argument("--attempts", type=int, default=3, help="probes per channel")
    parser.add_argument("--timeout", type=int, default=12, help="seconds per probe")
    parser.add_argument("--pause", type=int, default=5, help="seconds between probes")
    parser.add_argument("--workers", type=int, default=8, help="channels probed at once")
    args = parser.parse_args()

    names = args.lists or sorted(f[:-3] for f in os.listdir(LISTS_DIR) if f.endswith(".md"))

    dead_total = 0
    for name in names:
        results = check_list(name, args.attempts, args.timeout, args.pause, args.workers)
        dead_total += report(name, results, args.attempts)

    return 1 if dead_total else 0


if __name__ == "__main__":
    sys.exit(main())
