#!/usr/bin/python3

import os
import re

EPG_LIST = open('epglist.txt',"r") # for a clean code 

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
    dir_playlists = 'playlists'
    if not (os.path.isdir(dir_playlists)):
        os.mkdir(dir_playlists)
    with open("playlist.m3u8", "w", encoding='utf-8') as playlist:
        processed_epg_list = ", ".join(EPG_LIST).replace('\n', '')
        head_playlist = f'#EXTM3U x-tvg-url="{processed_epg_list}"'
        print(f'#EXTM3U x-tvg-url="{processed_epg_list}"', file=playlist)
        os.chdir("lists")
        for filename in sorted(os.listdir(".")):
            if filename == "README.md" or not filename.endswith(".md"):
                continue
            with open(filename, encoding='utf-8') as markup_file:
                file_country = os.path.join("..", dir_playlists, "playlist_" + filename[:-3:] + ".m3u8")
                playlist_country = open(file_country, "w", encoding='utf-8')
                playlist_country.write(head_playlist + "\n")
                group = filename.replace(".md", "").title()
                print(f"Generating {group}")
                for line in markup_file:
                    if "<h1>" in line.lower() and "</h1>" in line.lower():
                        group = re.sub('<[^<>]+>', '', line.strip())
                    if not "[>]" in line:
                        continue
                    channel = Channel(group, line)
                    print(channel.to_m3u_line(), file=playlist)
                    print(channel.to_m3u_line(), file=playlist_country)
                playlist_country.close()

if __name__ == "__main__":
    main()
