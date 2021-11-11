import sys
from typing import Text
import yaml
import os
import requests
import urllib3
from xml.etree import ElementTree
from pathlib import Path
from tqdm import tqdm

list_of_games = []
game_ids = []

def check_platform():
	if sys.platform.startswith("freebsd"):
		return "freebsd"
	elif sys.platform.startswith("linux"):
		return "linux"
	elif sys.platform.startswith("win32"):
		return "windows"

if check_platform() == "linux" or check_platform() == "freebsd":
	game_update_directory = str(Path.home()) + "/PS3 Game Updates"
elif check_platform() == "windows":
	game_update_directory = str(Path.home()) + "\PS3 Game Updates"

def convert_bytes_to_megabytes(size):
    size = int(float(size))/1024.0**2
    return ("%.2f") % size

def file_exists(path):
    if os.path.isfile(path) == True:
        return True
    else:
        return False

def folder_exists(path):
    if os.path.isdir(path) == True:
        return True
    else:
        return False

def read_game_ids(id):
    if file_exists(id) == True and Path(id).name == "games.yml":
        with open(id, "r") as games_yml:
            data = yaml.safe_load(games_yml)
            for i in data.keys():
                game_ids.append(i)
    elif len(id) == 9:
        gameid = id[0:4].upper()
        gameid = gameid + id[4:]

	# valid ids
        if gameid[0:4] == "BCAS" and gameid[4:].isdecimal() == True:
            game_ids.append(gameid)
        elif gameid[0:4] == "BCAX" and gameid[4:].isdecimal() == True:
            game_ids.append(gameid)
        elif gameid[0:4] == "BCED" and gameid[4:].isdecimal() == True:
            game_ids.append(gameid)
        elif gameid[0:4] == "BCES" and gameid[4:].isdecimal() == True:
            game_ids.append(gameid)
        elif gameid[0:4] == "BCJB" and gameid[4:].isdecimal() == True:
            game_ids.append(gameid)
        elif gameid[0:4] == "BCJS" and gameid[4:].isdecimal() == True:
            game_ids.append(gameid)
        elif gameid[0:4] == "BCKS" and gameid[4:].isdecimal() == True:
            game_ids.append(gameid)
        elif gameid[0:4] == "BCUS" and gameid[4:].isdecimal() == True:
            game_ids.append(gameid)
        elif gameid[0:4] == "BLAS" and gameid[4:].isdecimal() == True:
            game_ids.append(gameid)
        elif gameid[0:4] == "BLES" and gameid[4:].isdecimal() == True:
            game_ids.append(gameid)
        elif gameid[0:4] == "BLJM" and gameid[4:].isdecimal() == True:
            game_ids.append(gameid)
        elif gameid[0:4] == "BLJS" and gameid[4:].isdecimal() == True:
            game_ids.append(gameid)
        elif gameid[0:4] == "BLJX" and gameid[4:].isdecimal() == True:
            game_ids.append(gameid)
        elif gameid[0:4] == "BLKS" and gameid[4:].isdecimal() == True:
            game_ids.append(gameid)
        elif gameid[0:4] == "BLUD" and gameid[4:].isdecimal() == True:
            game_ids.append(gameid)
        elif gameid[0:4] == "BLUS" and gameid[4:].isdecimal() == True:
            game_ids.append(gameid)
        elif gameid[0:4] == "MRTC" and gameid[4:].isdecimal() == True:
            game_ids.append(gameid)
        elif gameid[0:4] == "NPEA" and gameid[4:].isdecimal() == True:
            game_ids.append(gameid)
        elif gameid[0:4] == "NPUB" and gameid[4:].isdecimal() == True:
            game_ids.append(gameid)
        elif gameid[0:4] == "NPUA" and gameid[4:].isdecimal() == True:
            game_ids.append(gameid)
        elif gameid[0:4] == "NPEB" and gameid[4:].isdecimal() == True:
            game_ids.append(gameid)
        elif gameid[0:4] == "NPJB" and gameid[4:].isdecimal() == True:
            game_ids.append(gameid)
        elif gameid[0:4] == "NPIA" and gameid[4:].isdecimal() == True:
            game_ids.append(gameid)
        elif gameid[0:4] == "NPJA" and gameid[4:].isdecimal() == True:
            game_ids.append(gameid)
        elif gameid[0:4] == "NPHA" and gameid[4:].isdecimal() == True:
            game_ids.append(gameid)
        else:
            print("Unknown game id: " + gameid)

    else:
        print("Game ID or the path to games.yml is incorrect")
        sys.exit(1)

def read_game_data():
    # this is required for the PlayStation's game update server
    # as it uses self signed signatures and also SSL verification
    # has to be disabled as well
    urllib3.disable_warnings()

    for i in game_ids:
        print("Processing: " + i)
        game = {
            "id": "",
            "name": "",
            "updates_url": [],
            "updates_size": [],
            "updates_sysver": [],
            "updates_version": [],
        }

        resp = requests.get("https://a0.ww.np.dl.playstation.net/tpl/np/" + i + "/" + i + "-ver.xml", verify=False)
        if resp.content == b'' or resp.status_code == 404:
            print("No data found for game ID: " + i + " - Skipping")
            continue
        tree = ElementTree.fromstring(resp.content)

        game['id'] = tree.get('titleid')
        for j in tree.find('tag').findall('package'):
            game['updates_version'].append(j.get('version'))
            game['updates_size'].append(convert_bytes_to_megabytes(j.get('size')))
            game['updates_sysver'].append(j.get('ps3_system_ver'))
            game['updates_url'].append(j.get('url'))

            if j.find('paramsfo') != None:
                game['name'] = j.find('paramsfo').find('TITLE').text

        list_of_games.append(game)

def download_game_updates():
    # this is required for the PlayStation's game update server
    # as it uses self signed signatures and also SSL verification
    # has to be disabled as well
    urllib3.disable_warnings()

    if folder_exists(game_update_directory) == False:
        print("Creating directory " + game_update_directory)
        path = Path(game_update_directory)
        path.mkdir(parents=True)

    for i in list_of_games:
        print("Downloading game updates: " + i['name'] + " (" + i['id'] + ")")

        if check_platform() == "linux" or check_platform() == "freebsd":
            if folder_exists(game_update_directory + "/" + i['id']) == False:
                gamedir = Path(game_update_directory + "/" + i['id'])
                gamedir.mkdir()
        elif check_platform() == "win32":
            if folder_exists(game_update_directory + "\\" + i['id']) == False:
                gamedir = Path(game_update_directory + "\\" + i['id'])
                gamedir.mkdir()


        for j in i['updates_url']:
            filename = j.split('/')[-1]

            if check_platform() == "linux" or check_platform() == "freebsd":
                if file_exists(game_update_directory + "/" + i['id'] + "/" + filename) == True:
                    print("Game update '" + filename + "' already downloaded - Skipping")
                    continue
            elif check_platform() == "win32":
                if file_exists(game_update_directory + "\\" + i['id'] + "\\" + filename) == True:
                    print("Game update '" + filename + "' already downloaded - Skipping")
                    continue

            with requests.get(j, stream=True) as resp:
                resp.raise_for_status()

                length = int(resp.headers.get('content-length', 0))
                if check_platform() == "linux" or check_platform() == "freebsd":
                    with open(game_update_directory + "/" + i['id'] + "/" + filename, 'wb') as f, tqdm(
                        desc=filename,
                        total=length,
                        unit='iB',
                        unit_scale=True,
                        unit_divisor=1024,
                    ) as bar:
                        for chunk in resp.iter_content(chunk_size=8192):
                            size = f.write(chunk)
                            bar.update(size)
                elif check_platform() == "win32":
                    with open(game_update_directory + "\\" + i['id'] + "\\" + filename, 'wb') as f, tqdm(
                        desc=filename,
                        total=length,
                        unit='iB',
                        unit_scale=True,
                        unit_divisor=1024,
                    ) as bar:
                        for chunk in resp.iter_content(chunk_size=8192):
                            size = f.write(chunk)
                            bar.update(size)

    print("Download complete")


def main():
    print("rgudw.py (v0.1)")
    if len(sys.argv) < 2:
        print("usage: rgudw.py [path/to/games.yml] || [GAMEID]")
    elif len(sys.argv) >= 3:
        print("usage: rgudw.py [path/to/games.yml] || [GAMEID]")
    else:
        print()
        print("-> Reading game ids")
        read_game_ids(sys.argv[1])
        print()
        print("-> Reading game data")
        read_game_data()
        print()
        print("-> Downloading game updates")
        download_game_updates()


if __name__ == "__main__":
    main()
