#!/usr/bin/python3

import os
import re

EPG_LIST = ( "https://iptv-org.github.io/epg/guides/ad/andorradifusio.ad.epg.xml",
             "https://iptv-org.github.io/epg/guides/ae-ar/osn.com.epg.xml",
             "https://iptv-org.github.io/epg/guides/af/arianaafgtv.com.epg.xml",
             "https://iptv-org.github.io/epg/guides/af/arianatelevision.com.epg.xml",
             "https://iptv-org.github.io/epg/guides/al/ipko.com.epg.xml",
             "https://iptv-org.github.io/epg/guides/am/tv.mail.ru.epg.xml",
             "https://iptv-org.github.io/epg/guides/ao/guide.dstv.com.epg.xml",
             "https://iptv-org.github.io/epg/guides/ar/directv.com.ar.epg.xml",
             "https://iptv-org.github.io/epg/guides/ar/mi.tv.epg.xml",
             "https://iptv-org.github.io/epg/guides/at/magentatv.at.epg.xml",
             "https://iptv-org.github.io/epg/guides/au/ontvtonight.com.epg.xml",
             "https://iptv-org.github.io/epg/guides/az/tv.mail.ru.epg.xml",
             "https://iptv-org.github.io/epg/guides/ba/mtel.ba.epg.xml",
             "https://iptv-org.github.io/epg/guides/be/telenettv.be.epg.xml",
             "https://iptv-org.github.io/epg/guides/bf/canalplus-afrique.com.epg.xml",
             "https://iptv-org.github.io/epg/guides/bg/tv.dir.bg.epg.xml",
             "https://iptv-org.github.io/epg/guides/bi/startimestv.com.epg.xml",
             "https://iptv-org.github.io/epg/guides/bl/canalplus-caraibes.com.epg.xml",
             "https://iptv-org.github.io/epg/guides/bo/comteco.com.bo.epg.xml",
             "https://iptv-org.github.io/epg/guides/br/mi.tv.epg.xml",
             "https://iptv-org.github.io/epg/guides/bs/rev.bs.epg.xml",
             "https://iptv-org.github.io/epg/guides/by/tv.mail.ru.epg.xml",
             "https://iptv-org.github.io/epg/guides/ca/tvhebdo.com.epg.xml",
             "https://iptv-org.github.io/epg/guides/ca/tvtv.us.epg.xml",
             "https://iptv-org.github.io/epg/guides/cd/startimestv.com.epg.xml",
             "https://iptv-org.github.io/epg/guides/ch/tv.blue.ch.epg.xml",
             "https://iptv-org.github.io/epg/guides/cl/gatotv.com.epg.xml",
             "https://iptv-org.github.io/epg/guides/cl/mi.tv.epg.xml",
             "https://iptv-org.github.io/epg/guides/cn/tv.cctv.com.epg.xml",
             "https://iptv-org.github.io/epg/guides/co/gatotv.com.epg.xml",
             "https://iptv-org.github.io/epg/guides/co/mi.tv.epg.xml",
             "https://iptv-org.github.io/epg/guides/co/siba.com.co.epg.xml",
             "https://iptv-org.github.io/epg/guides/cz/m.tv.sms.cz.epg.xml",
             "https://iptv-org.github.io/epg/guides/de/hd-plus.de.epg.xml",
             "https://iptv-org.github.io/epg/guides/de/horizon.tv.epg.xml",
             "https://iptv-org.github.io/epg/guides/dk/allente.se.epg.xml",
             "https://iptv-org.github.io/epg/guides/do/gatotv.com.epg.xml",
             "https://iptv-org.github.io/epg/guides/ec/gatotv.com.epg.xml",
             "https://iptv-org.github.io/epg/guides/ee-en/teliatv.ee.epg.xml",
             "https://iptv-org.github.io/epg/guides/eg-ar/elcinema.com.epg.xml",
             "https://iptv-org.github.io/epg/guides/es/gatotv.com.epg.xml",
             "https://iptv-org.github.io/epg/guides/es/movistarplus.es.epg.xml",
             "https://iptv-org.github.io/epg/guides/et/guide.dstv.com.epg.xml",
             "https://iptv-org.github.io/epg/guides/fi/telkussa.fi.epg.xml",
             "https://iptv-org.github.io/epg/guides/fo/kvf.fo.epg.xml",
             "https://iptv-org.github.io/epg/guides/fr/canalplus.com.epg.xml",
             "https://iptv-org.github.io/epg/guides/fr/chaines-tv.orange.fr.epg.xml",
             "https://iptv-org.github.io/epg/guides/fr/programme-tv.net.epg.xml",
             "https://iptv-org.github.io/epg/guides/fr/telecablesat.fr.epg.xml",
             "https://iptv-org.github.io/epg/guides/ga/startimestv.com.epg.xml",
             "https://iptv-org.github.io/epg/guides/ge/magticom.ge.epg.xml",
             "https://iptv-org.github.io/epg/guides/gr/cosmote.gr.epg.xml",
             "https://iptv-org.github.io/epg/guides/gt/gatotv.com.epg.xml",
             "https://iptv-org.github.io/epg/guides/gt/mi.tv.epg.xml",
             "https://iptv-org.github.io/epg/guides/hk-en/nowplayer.now.com.epg.xml",
             "https://iptv-org.github.io/epg/guides/hn/gatotv.com.epg.xml",
             "https://iptv-org.github.io/epg/guides/hn/mi.tv.epg.xml",
             "https://iptv-org.github.io/epg/guides/hr/maxtv.hrvatskitelekom.hr.epg.xml",
             "https://iptv-org.github.io/epg/guides/hu/mediaklikk.hu.epg.xml",
             "https://iptv-org.github.io/epg/guides/hu/musor.tv.epg.xml",
             "https://iptv-org.github.io/epg/guides/id-en/mncvision.id.epg.xml",
             "https://iptv-org.github.io/epg/guides/id/transvision.co.id.epg.xml",
             "https://iptv-org.github.io/epg/guides/id/vidio.com.epg.xml",
             "https://iptv-org.github.io/epg/guides/ie/ontvtonight.com.epg.xml",
             "https://iptv-org.github.io/epg/guides/il/9tv.co.il.epg.xml",
             "https://iptv-org.github.io/epg/guides/il/i24news.tv.epg.xml",
             "https://iptv-org.github.io/epg/guides/il/kan.org.il.epg.xml",
             "https://iptv-org.github.io/epg/guides/in/dishtv.in.epg.xml",
             "https://iptv-org.github.io/epg/guides/it/guidatv.sky.it.epg.xml",
             "https://iptv-org.github.io/epg/guides/it/mediaset.it.epg.xml",
             "https://iptv-org.github.io/epg/guides/jp/tvguide.myjcom.jp.epg.xml",
             "https://iptv-org.github.io/epg/guides/km/canalplus-reunion.com.epg.xml",
             "https://iptv-org.github.io/epg/guides/kr/seezntv.com.epg.xml",
             "https://iptv-org.github.io/epg/guides/kr/wavve.com.epg.xml",
             "https://iptv-org.github.io/epg/guides/kz/tv.yandex.ru.epg.xml",
             "https://iptv-org.github.io/epg/guides/mk/maxtvgo.mk.epg.xml",
             "https://iptv-org.github.io/epg/guides/mt/melita.com.epg.xml",
             "https://iptv-org.github.io/epg/guides/mw/guide.dstv.com.epg.xml",
             "https://iptv-org.github.io/epg/guides/mx/gatotv.com.epg.xml",
             "https://iptv-org.github.io/epg/guides/my/astro.com.my.epg.xml",
             "https://iptv-org.github.io/epg/guides/mz/guide.dstv.com.epg.xml",
             "https://iptv-org.github.io/epg/guides/ng/dstv.com.epg.xml",
             "https://iptv-org.github.io/epg/guides/ni/gatotv.com.epg.xml",
             "https://iptv-org.github.io/epg/guides/nl/delta.nl.epg.xml",
             "https://iptv-org.github.io/epg/guides/nl/ziggogo.tv.epg.xml",
             "https://iptv-org.github.io/epg/guides/no/allente.se.epg.xml",
             "https://iptv-org.github.io/epg/guides/no/frikanalen.no.epg.xml",
             "https://iptv-org.github.io/epg/guides/pa/gatotv.com.epg.xml",
             "https://iptv-org.github.io/epg/guides/pe/gatotv.com.epg.xml",
             "https://iptv-org.github.io/epg/guides/pe/mi.tv.epg.xml",
             "https://iptv-org.github.io/epg/guides/ph/clickthecity.com.epg.xml",
             "https://iptv-org.github.io/epg/guides/pl/programtv.onet.pl.epg.xml",
             "https://iptv-org.github.io/epg/guides/pt/meo.pt.epg.xml",
             "https://iptv-org.github.io/epg/guides/py/gatotv.com.epg.xml",
             "https://iptv-org.github.io/epg/guides/qa/bein.com.epg.xml",
             "https://iptv-org.github.io/epg/guides/ro/programetv.ro.epg.xml",
             "https://iptv-org.github.io/epg/guides/rs/mts.rs.epg.xml",
             "https://iptv-org.github.io/epg/guides/ru/tv.yandex.ru.epg.xml",
             "https://iptv-org.github.io/epg/guides/se/allente.se.epg.xml",
             "https://iptv-org.github.io/epg/guides/se/tv.nu.epg.xml",
             "https://iptv-org.github.io/epg/guides/sg/mewatch.sg.epg.xml",
             "https://iptv-org.github.io/epg/guides/sg/starhubtvplus.com.epg.xml",
             "https://iptv-org.github.io/epg/guides/si/tv2go.t-2.net.epg.xml",
             "https://iptv-org.github.io/epg/guides/sv/mi.tv.epg.xml",
             "https://iptv-org.github.io/epg/guides/th/tv.trueid.net.epg.xml",
             "https://iptv-org.github.io/epg/guides/tr/digiturk.com.tr.epg.xml",
             "https://iptv-org.github.io/epg/guides/tr/dsmart.com.tr.epg.xml",
             "https://iptv-org.github.io/epg/guides/tr/tvplus.com.tr.epg.xml",
             "https://iptv-org.github.io/epg/guides/tz/startimestv.com.epg.xml",
             "https://iptv-org.github.io/epg/guides/uk/bt.com.epg.xml",
             "https://iptv-org.github.io/epg/guides/uk/ontvtonight.com.epg.xml",
             "https://iptv-org.github.io/epg/guides/uk/sky.com.epg.xml",
             "https://iptv-org.github.io/epg/guides/uk/virginmedia.com.epg.xml",
             "https://iptv-org.github.io/epg/guides/us-local/tvtv.us.epg.xml",
             "https://iptv-org.github.io/epg/guides/us-pluto/i.mjh.nz.epg.xml",
             "https://iptv-org.github.io/epg/guides/us/directv.com.epg.xml",
             "https://iptv-org.github.io/epg/guides/us/ontvtonight.com.epg.xml",
             "https://iptv-org.github.io/epg/guides/us/tvguide.com.epg.xml",
             "https://iptv-org.github.io/epg/guides/us/tvtv.us.epg.xml",
             "https://iptv-org.github.io/epg/guides/za/guide.dstv.com.epg.xml",
           )

class Channel():

    def __init__(self, group, md_line):
        self.group = group
        md_line = md_line.strip()
        try:
            (before, number, name, url, logo, epg, after) = md_line.split("|")
        except ValueError:
            (before, number, name, url, logo, after) = md_line.split("|")
            epg = None
        self.number = number.strip()
        self.name = name.strip()
        self.url = url.strip()
        self.url = self.url[self.url.find("(")+1:self.url.rfind(")")]
        self.logo = logo.strip()
        self.logo = self.logo[self.logo.find('src="')+5:self.logo.rfind('"')]
        self.epg = epg.strip() if epg else None

    def to_m3u_line(self):
        if self.epg is None:
            return (f'#EXTINF:-1 tvg-name="{self.name}" tvg-logo="{self.logo}" group-title="{self.group}",{self.name}\n{self.url}')
        else:
            return (f'#EXTINF:-1 tvg-name="{self.name}" tvg-logo="{self.logo}" tvg-id="{self.epg}" group-title="{self.group}",{self.name}\n{self.url}')

if __name__ == "__main__":
    with open("playlist.m3u8", "w", encoding='utf-8') as playlist:
        print(f'#EXTM3U x-tvg-url="{",".join(EPG_LIST)}"', file=playlist)
        for filename in sorted(os.listdir(".")):
            if filename == "README.md" or not filename.endswith(".md"):
                continue
            with open(filename, encoding='utf-8') as markup_file:
                group = filename.replace(".md", "").title()
                print(f"Generating {group}")
                for line in markup_file:
                    if "<h1>" in line.lower() and "</h1>" in line.lower():
                        group = re.sub('<[^<>]+>', '', line.strip())
                    if not "[>]" in line:
                        continue
                    channel = Channel(group, line)
                    print(channel.to_m3u_line(), file=playlist)
