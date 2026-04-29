#!/usr/bin/python3

import os
import re

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
    "kenya": "KE",
    "korea": "KR",
    "kosovo": "XK",
    "latvia": "LV",
    "lithuania": "LT",
    "luxembourg": "LU",
    "macau": "MO",
    "malta": "MT",
    "mexico": "MX",
    "moldova": "MD",
    "monaco": "MC",
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
    "uk": "GB",
    "ukraine": "UA",
    "united_arab_emirates": "AE",
    "usa": "US",
    "usa_vod": "US",
    "venezuela": "VE",
}


class Channel:
    def __init__(self, group, md_line, country_code=""):
        self.group = group
        self.country_code = country_code
        md_line = md_line.strip()
        parts = md_line.split("|")
        self.number = parts[1].strip()
        self.name = parts[2].strip()
        self.url = parts[3].strip()
        self.url = self.url[self.url.find("(")+1:self.url.rfind(")")]
        self.logo = parts[4].strip()
        self.logo = self.logo[self.logo.find('src="')+5:self.logo.rfind('"')]

        self.chno = self.number if self.number and self.number != "0" else None
        
        if len(parts) > 6:
            self.epg = parts[5].strip()
        else:
            self.epg = None

    def to_m3u_line(self):
        country = f' tvg-country="{self.country_code}"' if self.country_code else ""
        chno = f' tvg-chno="{self.chno}"' if self.chno else ""
        if self.epg is None:
            return (f'#EXTINF:-1 tvg-name="{self.name}" tvg-logo="{self.logo}"{chno}{country} group-title="{self.group}",{self.name}\n{self.url}')
        else:
            return (f'#EXTINF:-1 tvg-name="{self.name}" tvg-logo="{self.logo}" tvg-id="{self.epg}"{chno}{country} group-title="{self.group}",{self.name}\n{self.url}')


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    lists_dir = os.path.join(base_dir, "lists")
    dir_playlists = os.path.join(base_dir, "playlists")

    if not os.path.isdir(dir_playlists):
        os.mkdir(dir_playlists)

    with open(os.path.join(base_dir, "epglist.txt"), encoding='utf-8') as epg_file:
        epg_urls = [line.strip() for line in epg_file if line.strip()]
    processed_epg_list = ", ".join(epg_urls)
    head_playlist = f'#EXTM3U x-tvg-url="{processed_epg_list}"\n'

    with open(os.path.join(base_dir, "playlist.m3u8"), "w", encoding='utf-8') as playlist:
        playlist.write(head_playlist)
        for filename in sorted(os.listdir(lists_dir)):
            if filename == "README.md" or not filename.endswith(".md"):
                continue
            markup_path = os.path.join(lists_dir, filename)
            country_path = os.path.join(dir_playlists, "playlist_" + filename[:-3] + ".m3u8")
            country_key = filename[:-3]
            group = country_key.replace("_", " ").title()
            country_code = COUNTRY_CODES.get(country_key, "")
            print(f"Generating {group}")
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
                    print(m3u_line, file=playlist)
                    print(m3u_line, file=playlist_country)

if __name__ == "__main__":
    main()
