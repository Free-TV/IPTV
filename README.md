Free TV
=======

This is an M3U playlist for free TV channels around the World.

Either free locally (over the air):

<img src="https://hatscripts.github.io/circle-flags/flags/gb.svg" width="24"> <img src="https://hatscripts.github.io/circle-flags/flags/us.svg" width="24"> <img src="https://hatscripts.github.io/circle-flags/flags/ca.svg" width="24"> <img src="https://hatscripts.github.io/circle-flags/flags/au.svg" width="24"> <img src="https://hatscripts.github.io/circle-flags/flags/ie.svg" width="24"> <img src="https://hatscripts.github.io/circle-flags/flags/es.svg" width="24"> <img src="https://hatscripts.github.io/circle-flags/flags/mx.svg" width="24"> <img src="https://hatscripts.github.io/circle-flags/flags/ar.svg" width="24"> <img src="https://hatscripts.github.io/circle-flags/flags/py.svg" width="24"> <img src="https://hatscripts.github.io/circle-flags/flags/tt.svg" width="24"> <img src="https://hatscripts.github.io/circle-flags/flags/de.svg" width="24"> <img src="https://hatscripts.github.io/circle-flags/flags/at.svg" width="24"> <img src="https://hatscripts.github.io/circle-flags/flags/fr.svg" width="24"> <img src="https://hatscripts.github.io/circle-flags/flags/be.svg" width="24"> <img src="https://hatscripts.github.io/circle-flags/flags/nl.svg" width="24"> <img src="https://hatscripts.github.io/circle-flags/flags/ch.svg" width="24"> <img src="https://hatscripts.github.io/circle-flags/flags/it.svg" width="24"> <img src="https://hatscripts.github.io/circle-flags/flags/sm.svg" width="24"> <img src="https://hatscripts.github.io/circle-flags/flags/tr.svg" width="24"> <img src="https://hatscripts.github.io/circle-flags/flags/gr.svg" width="24"> <img src="https://hatscripts.github.io/circle-flags/flags/sk.svg" width="24"> <img src="https://hatscripts.github.io/circle-flags/flags/si.svg" width="24"> <img src="https://hatscripts.github.io/circle-flags/flags/mt.svg" width="24"> <img src="https://hatscripts.github.io/circle-flags/flags/se.svg" width="24"> <img src="https://hatscripts.github.io/circle-flags/flags/dk.svg" width="24"> <img src="https://hatscripts.github.io/circle-flags/flags/fi.svg" width="24"> <img src="https://hatscripts.github.io/circle-flags/flags/hu.svg" width="24"> <img src="https://hatscripts.github.io/circle-flags/flags/cz.svg" width="24"> <img src="https://hatscripts.github.io/circle-flags/flags/ro.svg" width="24"> <img src="https://hatscripts.github.io/circle-flags/flags/ru.svg" width="24"> <img src="https://hatscripts.github.io/circle-flags/flags/by.svg" width="24"> <img src="https://hatscripts.github.io/circle-flags/flags/ua.svg" width="24"> <img src="https://hatscripts.github.io/circle-flags/flags/ee.svg" width="24"> <img src="https://hatscripts.github.io/circle-flags/flags/pt.svg" width="24"> <img src="https://hatscripts.github.io/circle-flags/flags/br.svg" width="24"> <img src="https://hatscripts.github.io/circle-flags/flags/in.svg" width="24"> <img src="https://hatscripts.github.io/circle-flags/flags/cn.svg" width="24"> <img src="https://hatscripts.github.io/circle-flags/flags/jp.svg" width="24"> <img src="https://hatscripts.github.io/circle-flags/flags/kr.svg" width="24"> <img src="https://hatscripts.github.io/circle-flags/flags/iq.svg" width="24"> <img src="https://hatscripts.github.io/circle-flags/flags/ir.svg" width="24">

Or free on the Internet:

- Plex TV
- Pluto TV (English, Spanish, French, Italian)
- Redbox Live TV
- Roku TV
- Samsung TV Plus
- Youtube live channels

To use it point your IPTV player to https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8.

Philosophy
==========

The main goals for this playlist are listed below.

**Quality over quantity**

The less channels we support the better.

- All channels should work well.
- As much as possible channels should be in HD, not SD.
- Only one URL per channel (no +1, no alternate feeds, no regional declinations)

**Only free channels**

If a channel is normally only available via commercial subscriptions it has nothing to do in this playlist. If on the other hand it is provided for free to everybody in a particular country, then it should be in this playlist.

- No paid channels
- Only channels which are officially provided for free (via DVB-S, DVB-T, analog, etc..)

**Only mainstream channels**

This is a playlist for everybody.

- No adult channels
- No channels dedicated to any particular religion
- No channels dedicated to any particular political party
- No channels made for a country and funded by a different country

Feed sources
============

It can be quite hard to find up to date URLs, here's a list of sources:

- https://github.com/iptv-org/iptv/tree/master/streams
- https://github.com/iptv-restream/iptv-channels/tree/master/channels
- https://github.com/Onemars/iptv-1/tree/master/channels
- Youtube: As long as the channel is live and its URL doesn't change (check the age of the stream, the number of viewers..)
- Dailymotion: Same criteria as for youtube

Format
======

The m3u8 playlist is generated by `make_playlist.py`, using the `.md` files located in `lists`.

Each .md file represesnts a group. The `<h1>` line is used as the group title.

Only channels which URL column starts with `[>]` are included in the playlist.

Channels which are not in HD are marked with an `Ⓢ`.

Channels which use GeoIP blocking are marked with a `Ⓖ`.

Channels which are live Youtube channels are marked with a `Ⓨ`.

Issues
======

Only create issues for bugs and feature requests.

Do not create issues to add/edit or to remove channels. If you want to add/edit/remove channels, create a pull request directly.

Pull Requests
=============

**Only modify .md files**

If your Pull Request modifies channels, only modify .md files. Do not modify m3u8 files in your pull request.

**Adding a new Channel**

To add a new channel, make a Pull Request.

- In your Pull Request you need to provide information to show that the channel is free.
- Use imgur.com to host the channel logo and point to it.
- If you have a valid stream, add it and put `[>]` in front of it.
- If you don't have an stream for the channel, add `[x]()` in the url column and place your channel in the Invalid category.
- If you have a stream but it doesn't work well, put the channel in the Invalid category and put `[x]` in front of the url.
- If you're adding geoblocked URLs specify it in your PR and specify which country they're working in. The PR will only be merged if these URLs can be tested.

**Removing a Channel**

To remove a channel, make a Pull Request.

In your Pull Request you need to provide information to show that the channel is only available via a private paid subscription.

Note: Public taxes (whether national or regional, whether called TV License or not) do not constitute a private paid subscription.

If a stream is broken, simply move the channel to the invalid category and replace `[>]` with `[x]` in the url column.
