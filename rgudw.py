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

def read_game_ids(path):
    if (file_exists(path) == True):
        if Path(path).name == "games.yml":
            with open(path, "r") as games_yml:
                data = yaml.safe_load(games_yml)
                for i in data.keys():
                    game_ids.append(i)
    else:
        if Path(path).name != "games.yml":
            print(path + " is not a games.yml file")
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
        if (resp.content == b'' or resp.status_code == 404):
            print("No data found for game ID: " + i + " - Skipping")
            continue
        tree = ElementTree.fromstring(resp.content)

        game['id'] = tree.get('titleid')
        for j in tree.find('tag').findall('package'):
            game['updates_version'].append(j.get('version'))
            game['updates_size'].append(convert_bytes_to_megabytes(j.get('size')))
            game['updates_sysver'].append(j.get('ps3_system_ver'))
            game['updates_url'].append(j.get('url'))

            if (j.find('paramsfo') != None):
                game['name'] = j.find('paramsfo').find('TITLE').text

        list_of_games.append(game)

def download_game_updates():
    # this is required for the PlayStation's game update server
    # as it uses self signed signatures and also SSL verification
    # has to be disabled as well
    urllib3.disable_warnings()

    if (folder_exists(game_update_directory) == False):
        print("Creating directory " + game_update_directory)
        path = Path(game_update_directory)
        path.mkdir(parents=True)

    for i in list_of_games:
        print("Downloading game updates: " + i['name'] + " (" + i['id'] + ")")

        if (folder_exists(game_update_directory + "\\" + i['id']) == False):
            gamedir = Path(game_update_directory + "\\" + i['id'])
            gamedir.mkdir()

        for j in i['updates_url']:
            filename = j.split('/')[-1]
            if (file_exists(game_update_directory + "\\" + i['id'] + "\\" + filename) == True):
                print("Game update '" + filename + "' already downloaded - Skipping")
                continue

            with requests.get(j, stream=True) as resp:
                resp.raise_for_status()

                length = int(resp.headers.get('content-length', 0))
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
        print("usage: rgudw.py path/to/games.yml")
    elif len(sys.argv) >= 3:
        print("usage: rgudw.py path/to/games.yml")
    else:
        print()
        print("-> Reading games.yaml")
        read_game_ids(sys.argv[1])
        print()
        print("-> Reading game data")
        read_game_data()
        print()
        print("-> Downloading game updates")
        download_game_updates()


if __name__ == "__main__":
    main()