#!/usr/bin/python3
"""Generate M3U playlists from the markdown channel lists in lists/."""

import argparse
import os
import re
import sys

COUNTRY_CODES = {
    "albania": "AL",
    "andorra": "AD",
    "argentina": "AR",
    "armenia": "AM",
    "australia": "AU",
    "austria": "AT",
    "azerbaijan": "AZ",
    "belarus": "BY",
    "belgium": "BE",
    "bosnia_and_herzegovina": "BA",
    "brazil": "BR",
    "bulgaria": "BG",
    "canada": "CA",
    "chad": "TD",
    "chile": "CL",
    "china": "CN",
    "costa_rica": "CR",
    "croatia": "HR",
    "cyprus": "CY",
    "czech_republic": "CZ",
    "denmark": "DK",
    "dominican_republic": "DO",
    "egypt": "EG",
    "estonia": "EE",
    "faroe_islands": "FO",
    "finland": "FI",
    "france": "FR",
    "georgia": "GE",
    "germany": "DE",
    "greece": "GR",
    "greenland": "GL",
    "hong_kong": "HK",
    "hongkong": "HK",
    "hungary": "HU",
    "iceland": "IS",
    "india": "IN",
    "indonesia": "ID",
    "iran": "IR",
    "iraq": "IQ",
    "ireland": "IE",
    "israel": "IL",
    "italy": "IT",
    "japan": "JP",
    "kazakhstan": "KZ",
    "kenya": "KE",
    "korea": "KR",
    "kosovo": "XK",
    "latvia": "LV",
    "lebanon": "LB",
    "lithuania": "LT",
    "luxembourg": "LU",
    "macau": "MO",
    "malta": "MT",
    "mexico": "MX",
    "moldova": "MD",
    "monaco": "MC",
    "mongolia": "MN",
    "montenegro": "ME",
    "netherlands": "NL",
    "nigeria": "NG",
    "north_korea": "KP",
    "north_macedonia": "MK",
    "norway": "NO",
    "paraguay": "PY",
    "peru": "PE",
    "poland": "PL",
    "portugal": "PT",
    "qatar": "QA",
    "romania": "RO",
    "russia": "RU",
    "san_marino": "SM",
    "saudi_arabia": "SA",
    "serbia": "RS",
    "slovakia": "SK",
    "slovenia": "SI",
    "somalia": "SO",
    "spain": "ES",
    "spain_vod": "ES",
    "sweden": "SE",
    "switzerland": "CH",
    "taiwan": "TW",
    "trinidad": "TT",
    "turkey": "TR",
    "turkmenistan": "TM",
    "uk": "GB",
    "ukraine": "UA",
    "united_arab_emirates": "AE",
    "usa": "US",
    "usa_vod": "US",
    "venezuela": "VE",
}

ALIASES = {
    "alb": "albania",
    "aus": "australia",
    "aut": "austria",
    "bel": "belgium",
    "bgr": "bulgaria",
    "bih": "bosnia_and_herzegovina",
    "bra": "brazil",
    "can": "canada",
    "che": "switzerland",
    "chn": "china",
    "cyp": "cyprus",
    "cze": "czech_republic",
    "deu": "germany",
    "dnk": "denmark",
    "eng": "uk",
    "esp": "spain",
    "est": "estonia",
    "fin": "finland",
    "fra": "france",
    "gb": "uk",
    "gbr": "uk",
    "ger": "germany",
    "grc": "greece",
    "gre": "greece",
    "hrv": "croatia",
    "ind": "india",
    "irl": "ireland",
    "isr": "israel",
    "ita": "italy",
    "jpn": "japan",
    "kor": "korea",
    "ltu": "lithuania",
    "lux": "luxembourg",
    "lva": "latvia",
    "mkd": "north_macedonia",
    "mlt": "malta",
    "ned": "netherlands",
    "nld": "netherlands",
    "nor": "norway",
    "pol": "poland",
    "por": "portugal",
    "prk": "north_korea",
    "prt": "portugal",
    "rou": "romania",
    "rus": "russia",
    "srb": "serbia",
    "svk": "slovakia",
    "svn": "slovenia",
    "swe": "sweden",
    "tur": "turkey",
    "uae": "united_arab_emirates",
    "uk": "uk",
    "ukr": "ukraine",
    "us": "usa",
    "usa": "usa",
}


class Channel:  # pylint: disable=too-few-public-methods,too-many-instance-attributes
    """A single channel entry parsed from a markdown list line."""

    def __init__(self, group, md_line, country_code=""):
        self.group = group.replace('"', '')
        self.country_code = country_code
        md_line = md_line.strip()
        parts = md_line.split("|")
        self.number = parts[1].strip().replace('"', '')
        self.name = parts[2].strip().replace('"', '')
        self.url = parts[3].strip()
        self.url = self.url[self.url.find("(")+1:self.url.rfind(")")]
        self.logo = parts[4].strip()
        self.logo = self.logo[self.logo.find('src="')+5:self.logo.rfind('"')].replace('"', '')

        self.chno = self.number if self.number and self.number != "0" else None

        if len(parts) > 6:
            self.epg = parts[5].strip().replace('"', '')
        else:
            self.epg = None

    def to_m3u_line(self):
        """Render this channel as a #EXTINF entry followed by its URL."""
        country = f' tvg-country="{self.country_code}"' if self.country_code else ""
        chno = f' tvg-chno="{self.chno}"' if self.chno else ""
        epg = f' tvg-id="{self.epg}"' if self.epg is not None else ""
        # Strip trailing in-list markers (Ⓖ/Ⓢ/Ⓨ/...) from tvg-name so EPG
        # matching isn't broken by a symbol meant for human readers.
        tvg_name = re.sub(r'\s*[Ⓐ-ⓩ]+\s*$', '', self.name)
        return (
            f'#EXTINF:-1 tvg-name="{tvg_name}" tvg-logo="{self.logo}"{epg}{chno}{country}'
            f' group-title="{self.group}",{self.name}\n{self.url}'
        )


def generate_playlist(markup_path, country_path, country_key, country_code,
                      head_playlist, master_file=None):
    """Generate a single playlist from markup_path."""
    group = country_key.replace("_", " ").title()
    count = 0
    with open(markup_path, encoding='utf-8') as markup_file, \
         open(country_path, "w", encoding='utf-8') as playlist_country:
        playlist_country.write(head_playlist)
        for line in markup_file:
            if "<h1>" in line.lower() and "</h1>" in line.lower():
                group = re.sub('<[^<>]+>', '', line.strip())
            if "[>]" not in line:
                continue
            channel = Channel(group, line, country_code)
            m3u_line = channel.to_m3u_line()
            if master_file is not None:
                print(m3u_line, file=master_file)
            print(m3u_line, file=playlist_country)
            count += 1
    return count, group


def resolve_target(target, available_files):
    """Resolve a target string (code, name, filename) to matching .md filenames."""
    t = target.strip().lower()
    t = os.path.basename(t)
    if t.endswith(".md"):
        t = t[:-3]
    if t.endswith(".m3u8"):
        t = t[:-5]
    if t.startswith("playlist_"):
        t = t[9:]

    # 1. Exact key match (e.g. 'italy', 'zz_vod_it', 'usa')
    matches = [f for f in available_files if f[:-3].lower() == t]
    if matches:
        return matches

    # 2. Exact country code match (e.g. 'IT', 'US', 'ES', 'FR')
    matches = [f for f in available_files if COUNTRY_CODES.get(f[:-3], "").lower() == t]
    if matches:
        return matches

    # 3. Known alias match (e.g. 'ita', 'fra', 'gb', 'uae')
    if t in ALIASES:
        alias_key = ALIASES[t]
        matches = [f for f in available_files if f[:-3].lower() == alias_key]
        if matches:
            return matches

    # 4. Stripped 'zz_' prefix match (e.g. 'vod_it' -> 'zz_vod_it.md', 'movies' -> 'zz_movies.md')
    matches = [f for f in available_files if f[:-3].lower().startswith("zz_") and f[:-3].lower()[3:] == t]
    if matches:
        return matches

    # 5. Substring / partial match in list key (e.g. 'vod' -> spain_vod, usa_vod, zz_vod_it)
    matches = [f for f in available_files if t in f[:-3].lower()]
    if matches:
        return matches

    return []


def show_available(available_files):
    """Print available playlists and country codes."""
    country_files = [f for f in available_files if not f.startswith("zz_")]
    special_files = [f for f in available_files if f.startswith("zz_")]

    print(f"Liste Paesi disponibili ({len(country_files)}):")
    print(f"  {'Sigla':<7} {'Nome':<30} {'File':<25}")
    print("  " + "-" * 62)
    for f in country_files:
        key = f[:-3]
        code = COUNTRY_CODES.get(key, "-")
        name = key.replace("_", " ").title()
        print(f"  {code:<7} {name:<30} {f:<25}")

    print(f"\nListe Speciali / Tematiche ({len(special_files)}):")
    print(f"  {'Sigla/Alias':<15} {'Nome':<25} {'File':<25}")
    print("  " + "-" * 65)
    for f in special_files:
        key = f[:-3]
        alias = key[3:]
        name = key.replace("_", " ").title()
        print(f"  {alias:<15} {name:<25} {f:<25}")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Genera playlist M3U dai file markdown in lists/.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Esempi:
  python make_playlist.py                # Genera tutte le liste e playlist.m3u8 (default)
  python make_playlist.py it             # Genera solo playlist_italy.m3u8
  python make_playlist.py IT             # Genera solo playlist_italy.m3u8
  python make_playlist.py it fr de       # Genera playlist per Italia, Francia e Germania
  python make_playlist.py es             # Genera Spagna (playlist_spain e playlist_spain_vod)
  python make_playlist.py vod_it         # Genera playlist_zz_vod_it.m3u8
  python make_playlist.py -s             # Mostra l'elenco di tutte le sigle e liste disponibili
  python make_playlist.py it -m          # Genera Italia e aggiorna anche playlist.m3u8
""",
    )
    parser.add_argument(
        "targets",
        nargs="*",
        metavar="SIGLA",
        help="Sigla paese, nome o file della lista da generare (es. 'it', 'italy', 'es', 'vod_it'). "
             "Se omesso, genera tutte le liste e playlist.m3u8.",
    )
    parser.add_argument(
        "-a", "--all",
        action="store_true",
        help="Forza la generazione di tutte le liste e di playlist.m3u8.",
    )
    parser.add_argument(
        "-s", "--show", "--available",
        dest="show",
        action="store_true",
        help="Mostra l'elenco di tutte le sigle e liste disponibili ed esce.",
    )
    parser.add_argument(
        "-m", "--master",
        action="store_true",
        help="Aggiorna anche la playlist master globale (playlist.m3u8).",
    )
    parser.add_argument(
        "-l", "--list",
        dest="explicit_lists",
        action="append",
        metavar="SIGLA",
        help="Specifica una sigla/lista (alternativa agli argomenti posizionali).",
    )
    return parser.parse_args()


def main():  # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    """Build the combined playlist.m3u8 and/or selected per-country playlists."""
    args = parse_args()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    lists_dir = os.path.join(base_dir, "lists")
    dir_playlists = os.path.join(base_dir, "playlists")

    if not os.path.isdir(dir_playlists):
        os.mkdir(dir_playlists)

    available_files = sorted([
        f for f in os.listdir(lists_dir)
        if f.endswith(".md") and f != "README.md"
    ])

    if args.show:
        show_available(available_files)
        return 0

    with open(os.path.join(base_dir, "epglist.txt"), encoding='utf-8') as epg_file:
        epg_urls = [line.strip() for line in epg_file if line.strip()]
    processed_epg_list = ", ".join(epg_urls)
    head_playlist = f'#EXTM3U x-tvg-url="{processed_epg_list}"\n'

    requested_targets = (args.targets or []) + (args.explicit_lists or [])

    # If no targets specified or --all flag used: full rebuild
    if not requested_targets or args.all:
        with open(os.path.join(base_dir, "playlist.m3u8"), "w", encoding='utf-8') as playlist:
            playlist.write(head_playlist)
            for filename in available_files:
                markup_path = os.path.join(lists_dir, filename)
                country_key = filename[:-3]
                country_path = os.path.join(dir_playlists, f"playlist_{country_key}.m3u8")
                country_code = COUNTRY_CODES.get(country_key, "")
                group = country_key.replace("_", " ").title()
                print(f"Generating {group}")
                generate_playlist(
                    markup_path, country_path, country_key, country_code,
                    head_playlist, master_file=playlist
                )
        return 0

    # Targeted generation
    matched_files = []
    has_errors = False
    for target in requested_targets:
        matches = resolve_target(target, available_files)
        if not matches:
            print(f"Errore: nessuna lista trovata per '{target}'. Usa -s / --show per le sigle disponibili.",
                  file=sys.stderr)
            has_errors = True
        else:
            for m in matches:
                if m not in matched_files:
                    matched_files.append(m)

    if not matched_files:
        return 1

    # Optional: if --master was requested along with targeted lists, rebuild playlist.m3u8
    master_file = None
    if args.master:
        master_file = open(os.path.join(base_dir, "playlist.m3u8"), "w", encoding='utf-8')
        master_file.write(head_playlist)

    try:
        if args.master:
            # When master playlist is rebuilt, we iterate through all files for master_file,
            # but only rewrite individual playlist files for matched_files.
            for filename in available_files:
                markup_path = os.path.join(lists_dir, filename)
                country_key = filename[:-3]
                country_path = os.path.join(dir_playlists, f"playlist_{country_key}.m3u8")
                country_code = COUNTRY_CODES.get(country_key, "")
                if filename in matched_files:
                    count, group = generate_playlist(
                        markup_path, country_path, country_key, country_code,
                        head_playlist, master_file=master_file
                    )
                    rel_dest = os.path.relpath(country_path, base_dir)
                    print(f"Generating {group} ({count} canali) -> {rel_dest}")
                else:
                    # Only append to master_file without overwriting country playlist
                    country_group = country_key.replace("_", " ").title()
                    with open(markup_path, encoding='utf-8') as markup_file:
                        for line in markup_file:
                            if "<h1>" in line.lower() and "</h1>" in line.lower():
                                country_group = re.sub('<[^<>]+>', '', line.strip())
                            if "[>]" not in line:
                                continue
                            channel = Channel(country_group, line, country_code)
                            print(channel.to_m3u_line(), file=master_file)
            print("Aggiornata anche playlist.m3u8 (master)")
        else:
            for filename in matched_files:
                markup_path = os.path.join(lists_dir, filename)
                country_key = filename[:-3]
                country_path = os.path.join(dir_playlists, f"playlist_{country_key}.m3u8")
                country_code = COUNTRY_CODES.get(country_key, "")
                count, group = generate_playlist(
                    markup_path, country_path, country_key, country_code,
                    head_playlist, master_file=None
                )
                rel_dest = os.path.relpath(country_path, base_dir)
                print(f"Generating {group} ({count} canali) -> {rel_dest}")
    finally:
        if master_file is not None:
            master_file.close()

    return 1 if has_errors else 0


if __name__ == "__main__":
    sys.exit(main())
