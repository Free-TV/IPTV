#!/usr/bin/python3

import os
import re

class Channel():

    def __init__(self, group, md_line):
        self.group = group
        md_line = md_line.strip()
        (before, number, name, url, logo, after) = md_line.split("|")
        self.number = number.strip()
        self.name = name.strip()
        self.url = url.strip()
        self.url = self.url[self.url.find("(")+1:self.url.rfind(")")]
        self.logo = logo.strip()
        self.logo = self.logo[self.logo.find('src="')+5:self.logo.rfind('"')]

    def to_m3u_line(self):
        return('#EXTINF:-1 tvg-name="%(name)s" tvg-logo="%(logo)s" group-title="%(group)s",%(name)s\n%(url)s' \
            % {'name':self.name, 'logo':self.logo, 'group':self.group, 'url':self.url})


if __name__ == "__main__":
    with open("playlist.m3u8", "w") as playlist:
        print("#EXTM3U", file=playlist)
        for filename in sorted(os.listdir(".")):
            if filename == "README.md" or not filename.endswith(".md"):
                continue
            with open(filename) as markup_file:
                group = filename.replace(".md", "").title()
                for line in markup_file:
                    if "<h1>" in line.lower() and "</h1>" in line.lower():
                        group = re.sub('<[^<>]+>', '', line.strip())
                    if not "[>]" in line:
                        continue
                    channel = Channel(group, line)
                    print(channel.to_m3u_line(), file=playlist)

