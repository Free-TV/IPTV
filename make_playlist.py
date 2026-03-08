#!/usr/bin/python3

import os
import re


class Channel:
    def __init__(self, group, md_line):
        self.group = group
        md_line = md_line.strip()
        parts = md_line.split("|")
        self.number = parts[1].strip()
        self.name = parts[2].strip()
        self.url = parts[3].strip()
        self.url = self.url[self.url.find("(")+1:self.url.rfind(")")]
        self.logo = parts[4].strip()
        self.logo = self.logo[self.logo.find('src="')+5:self.logo.rfind('"')]
        if len(parts) > 6:
            self.epg = parts[5].strip()
        else:
            self.epg = None

    def to_m3u_line(self):
        if self.epg is None:
            return (f'#EXTINF:-1 tvg-name="{self.name}" tvg-logo="{self.logo}" group-title="{self.group}",{self.name}\n{self.url}')
        else:
            return (f'#EXTINF:-1 tvg-name="{self.name}" tvg-logo="{self.logo}" tvg-id="{self.epg}" group-title="{self.group}",{self.name}\n{self.url}')


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
            group = filename[:-3].replace("_", " ").title()
            print(f"Generating {group}")
            with open(markup_path, encoding='utf-8') as markup_file, \
                 open(country_path, "w", encoding='utf-8') as playlist_country:
                playlist_country.write(head_playlist)
                for line in markup_file:
                    if "<h1>" in line.lower() and "</h1>" in line.lower():
                        group = re.sub('<[^<>]+>', '', line.strip())
                    if "[>]" not in line:
                        continue
                    channel = Channel(group, line)
                    m3u_line = channel.to_m3u_line()
                    print(m3u_line, file=playlist)
                    print(m3u_line, file=playlist_country)

if __name__ == "__main__":
    main()
