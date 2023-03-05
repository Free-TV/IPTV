# converts playlist.m3u8 to playlists by country in the playlists folder
import os


def main():
    dir_playlists = 'playlists'
    # create folders for playlist countries
    if not (os.path.isdir(dir_playlists)):
        os.mkdir(dir_playlists)
    # convert playlist to playlist countries
    file_playlist = open("playlist.m3u8", "r", encoding='utf-8')
    country_curent = 'not'
    for line in file_playlist:
        if line[:7] == '#EXTM3U':
            head_playlist = line
        elif line[:7] == '#EXTINF':
            start_country = line.find('group-title') + 13
            end_country = line.find('"', start_country)
            country_new = line[start_country:end_country]
            if country_curent != country_new:
                if not(country_curent == 'not'):
                    file_playlist_country.close()
                country_curent = country_new
                file_playlist_country = open(dir_playlists + "\playlist_" + country_curent + ".m3u8", "w", encoding='utf-8')
                file_playlist_country.write(head_playlist)
                file_playlist_country.write(line)
            else:
                file_playlist_country.write(line)
        elif line[:4] == 'http':
            file_playlist_country.write(line)
    file_playlist_country.close()


if __name__ == "__main__":
    main()
