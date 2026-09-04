#!/usr/bin/python3
"""Report which channels in `lists/` are no longer reachable.

The playlist checker records the URLs it could not open, but a bare URL does not say
which channel or which list it came from, and one failed attempt does not mean a
channel is gone. Streams time out, rate limit, move between CDNs, and some are only
served inside their own country.

This script maps every URL back to its channel and list, probes each one several
times, and separates the cases that look alike from the outside:

  dead         every attempt said "not found", so the stream is really gone
  disputed     looked dead over HTTP, but ffprobe found a real audio/video stream
               behind it - needs a human, not a bot, to decide
  blocked      the server answered but refused us, which is what a channel served
               only in its own country looks like from anywhere else
  unreachable  every attempt timed out or failed to connect
  flaky        answered at least once, so it is up but unreliable from here
  alive        answered every time

Only `dead` is safe to act on without a second opinion. `blocked` in particular must
not be treated as a fault: the lists mark geo-blocked channels deliberately.

Both playlist formats used by the lists are understood, HLS (.m3u8) and MPEG-DASH
(.mpd), so a DASH stream is not mistaken for a broken one. Neither check is airtight
on its own: a manifest that starts with `#EXTM3U`/`<MPD` is not proof the media
behind it plays, and a payload ffprobe can decode is not proof it is a live channel
rather than a stray media fragment sitting at a familiar-looking URL - one such
fragment is what first prompted the --confirm-dead option below. Treat `dead` as
"nothing here answered like a stream, twice, two different ways" rather than proof.

With --confirm-dead, every channel that looks `dead` over HTTP gets a second,
independent opinion from `ffprobe` (part of ffmpeg) before being reported as dead:
ffprobe actually tries to decode audio/video from the URL, which catches streams a
header check alone cannot judge either way. This second opinion is one-directional -
it can only pull a channel *out* of `dead` into `disputed`, never push a channel that
looks fine over HTTP into a worse state - because a slow or unusual server can make
ffprobe time out on a channel that plays fine elsewhere (this happened while writing
this script: a known-good DASH channel needed longer than any reasonable per-channel
budget for ffprobe to open), and a timeout there must not be read as confirmation of
anything. It is off by default because it materially changes the runtime: ffprobe
does real network I/O per candidate, on top of the HTTP probes already spent finding
that candidate, and only makes sense where that time is available (a weekly run),
not where it is not (a PR check blocking on a handful of changed links).

Usage:
    ./check_channels.py                          # every list
    ./check_channels.py greece italy             # only those lists
    ./check_channels.py --attempts 5 greece      # more attempts per channel
    ./check_channels.py --confirm-dead greece    # + ffprobe second opinion on dead ones
"""

import argparse
import json
import os
import re
import shutil
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

LISTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lists")

# one bundle for the knobs every probe/list/run function otherwise had to repeat
ProbeSettings = namedtuple(
    "ProbeSettings", ["attempts", "timeout", "pause", "workers", "confirm_dead"],
)

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
DISPUTED = "disputed"
BLOCKED = "blocked"
UNREACHED = "unreachable"
FLAKY = "flaky"

# a channel served only in its own country answers, then refuses us
REFUSING_CODES = (401, 402, 403, 451)
GONE_CODES = (404, 410)

# ffprobe gets much longer than an HTTP probe: it has to open a connection, read
# enough of the stream to find a decodable frame, and do that over whatever the
# channel's own CDN feels like doing today, not just get a response header back
FFPROBE_TIMEOUT = 25


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


def ffprobe_finds_a_stream(url):
    """Ask ffprobe whether it can decode real audio/video from `url`.

    Returns True/False for a definite answer, or None if ffprobe itself could not
    be asked (missing binary, timed out, or errored) - None must never be treated
    as "no stream found", only as "no second opinion available this time".
    """
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-user_agent", USER_AGENT,
                "-show_entries", "stream=codec_type",
                "-of", "csv=p=0",
                url,
            ],
            capture_output=True, text=True, timeout=FFPROBE_TIMEOUT, check=False,
        )
    except subprocess.TimeoutExpired:
        return None
    except OSError:
        return None
    if result.returncode != 0:
        return False
    return any(kind in result.stdout for kind in ("video", "audio"))


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


def check(channel, settings):
    """Probe one channel `settings.attempts` times and return its state.

    If the channel looks dead and `settings.confirm_dead` is set, give it one more
    chance through ffprobe before reporting it as dead - see the module docstring
    for why this can only pull a verdict out of `dead`, never push one into it.
    """
    name, url = channel
    outcomes = []
    for attempt in range(settings.attempts):
        outcomes.append(probe(url, settings.timeout))
        if attempt + 1 < settings.attempts:
            time.sleep(settings.pause)
    state = classify(outcomes)
    if state == DEAD and settings.confirm_dead:
        if ffprobe_finds_a_stream(url):
            state = DISPUTED
    return name, url, state, outcomes


def check_all(names, settings):
    """Probe every channel of every named list and return `{list_name: [results]}`.

    All channels of all lists share one pool of `settings.workers`, so a run across
    many lists is not slower per list than a run of one - a list with two channels
    does not pay the same wall-clock floor as a list with two hundred just because
    it was handed its own pool that then sits mostly idle.
    """
    channels_by_list = {
        name: [c for c in read_channels(name) if not c[1].startswith("https://www.youtube.com")]
        for name in names
    }

    def run(item):
        list_name, channel = item
        return list_name, check(channel, settings)

    jobs = [(name, channel) for name, channels in channels_by_list.items() for channel in channels]
    results_by_list = {name: [] for name in names}
    with ThreadPoolExecutor(max_workers=settings.workers) as pool:
        for list_name, result in pool.map(run, jobs):
            results_by_list[list_name].append(result)
    return results_by_list


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


def as_records(list_name, results, checked_at, confirm_dead):
    """Turn one list's results into flat dicts, one per channel, for --json output.

    `confirm_dead` is recorded on every row so a later reader can tell a `dead`
    verdict that already survived an ffprobe second opinion from one that has not
    been asked yet - the two are not the same strength of evidence.
    """
    return [
        {
            "checked_at": checked_at,
            "list": list_name,
            "channel": channel,
            "url": url,
            "state": state,
            "outcomes": outcomes,
            "confirm_dead": confirm_dead,
        }
        for channel, url, state, outcomes in results
    ]


def parse_args():
    """Parse the command line into an `argparse.Namespace`."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("lists", nargs="*", help="lists to check, without the .md suffix")
    parser.add_argument("--attempts", type=int, default=3, help="probes per channel")
    parser.add_argument("--timeout", type=int, default=12, help="seconds per probe")
    parser.add_argument("--pause", type=int, default=5, help="seconds between probes")
    parser.add_argument("--workers", type=int, default=8, help="channels probed at once")
    parser.add_argument(
        "--confirm-dead", action="store_true",
        help="give ffprobe a second opinion on channels that look dead (slower; needs ffmpeg)",
    )
    parser.add_argument(
        "--json", metavar="PATH",
        help="also write every channel's result as one JSON record per line to PATH, for "
             "building a history across runs (state, outcomes, timestamp, list, channel, url)",
    )
    return parser.parse_args()


def write_json_records(handle, names, results_by_list, checked_at, confirm_dead):
    """Write every list's results to `handle` as one JSON record per channel per line."""
    for name in names:
        for record in as_records(name, results_by_list[name], checked_at, confirm_dead):
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def main():
    """Check the lists named on the command line, or every list."""
    args = parse_args()

    if args.confirm_dead and shutil.which("ffprobe") is None:
        print(
            "--confirm-dead needs ffprobe (part of ffmpeg) on PATH; proceeding without it.",
            file=sys.stderr,
        )
        args.confirm_dead = False

    all_lists = (f[:-3] for f in os.listdir(LISTS_DIR) if f.endswith(".md"))
    names = args.lists or sorted(all_lists)
    checked_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    settings = ProbeSettings(
        args.attempts, args.timeout, args.pause, args.workers, args.confirm_dead,
    )

    results_by_list = check_all(names, settings)

    dead_total = sum(report(name, results_by_list[name], args.attempts) for name in names)
    if args.json:
        with open(args.json, "w", encoding="utf-8") as handle:
            write_json_records(handle, names, results_by_list, checked_at, args.confirm_dead)

    return 1 if dead_total else 0


if __name__ == "__main__":
    sys.exit(main())
