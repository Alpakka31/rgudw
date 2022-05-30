# Libraries
import sys, os, yaml, requests, urllib3
from pathlib import Path
from xml.etree import ElementTree
from tqdm import tqdm

# Classes
class App:
  def __init__(self, name, version):
    self._name = name
    self._version = version

  def print_version(self):
    print(f"{self._name} ({self._version})")
  
  def get_platform(self, name):
    return sys.platform.startswith(name)
  
  def verify_platform(self):
    if self.get_platform("win32"):
      return str(Path.home()) + "\PS3 Game Updates"
    elif self.get_platform("freebsd") or self.get_platform("linux") or self.get_platform("darwin"):
      return str(Path.home()) + "/PS3 Game Updates"
    else:
      print(f"Unknown platform: {sys.platform}")
      exit(1)
  
  def show_usage(self):
    self.print_version()
    print(f"Usage: {self._name} [options]")
    print("  options:")
    print("    [path/to/games.yml]")
    print("    [ID]")

class Game:
  def __init__(self, id, name, url, size, sysver, version):
    self._id = id
    self._name = name
    self._url = url
    self._size = size
    self._sysver = sysver
    self._version = version
  
  # Getters
  @property
  def id(self):
    return self._id
  
  @property
  def name(self):
    return self._name
  
  @property
  def url(self):
    return self._url
  
  @property
  def size(self):
    return self._size
  
  @property
  def sysver(self):
    return self._sysver
  
  @property
  def version(self):
    return self._version

class GameProcessor:
  def __init__(self, app):
    self._game_updates_folder = str()
    self._game_list = []
    self._game_ids = []
    self._valid_ids = [
      "BCAS",
      "BCAX",
      "BCED",
      "BCES",
      "BCJB",
      "BCJS",
      "BCKS",
      "BCUS",
      "BLAS",
      "BLES",
      "BLJM",
      "BLJS",
      "BLJX",
      "BLKS",
      "BLUD",
      "BLUS",
      "MRTC",
      "NPEA",
      "NPUB",
      "NPUA",
      "NPEB",
      "NPJB",
      "NPIA",
      "NPJA",
      "NPHA"
    ]
    self._app = app

  def add_game(self, game):
    self._game_list.append(game)

  def add_game_id(self, id):
    self._game_ids.append(id)
  
  def print_game_list(self):
    print(self._game_list)
  
  def print_game_ids(self):
    print(self._game_ids)

  def validate_id(self, id):
    first_part = id[0:4].upper()
    last_part = id[4:]

    if first_part in self._valid_ids and last_part.isdecimal():
      self.add_game_id(first_part + last_part)
    else:
      print(f"Unknown ID: {first_part + last_part}")
      exit(1)
  
  def create_per_game_update_folder(self, id):
    if self._app.get_platform("win32"):
      if folder_exists(self._game_updates_folder + "\\" + id) == False:
        game_folder = Path(self._game_updates_folder + "\\" + id)
        game_folder.mkdir()
    elif self._app.get_platform("freebsd") or self._app.get_platform("linux") or self._app.get_platform("darwin"):
      if folder_exists(self._game_updates_folder + "/" + id) == False:
        game_folder = Path(self._game_updates_folder + "/" + id)
        game_folder.mkdir()

  # Getters
  @property
  def game_updates_folder(self):
    return self._game_updates_folder
  
  @property
  def game_ids(self):
    return self._game_ids
  
  @property
  def game_list(self):
    return self._game_list

  # Setters
  @game_updates_folder.setter
  def game_updates_folder(self, folder_path):
    self._game_updates_folder = folder_path


class MetadataParser:
  def __init__(self, processor, downloader):
    self._processor = processor
    self._downloader = downloader

  def parse_game_ids(self, game_id):
    print(f"Parsing ID(s)...")
    if file_exists(game_id) and Path(game_id).name == "games.yml":
      with open(game_id, "r") as games_yml:
        data = yaml.safe_load(games_yml)
        for id in data.keys():
          self._processor.add_game_id(id)
    elif len(game_id) == 9:
      self._processor.validate_id(game_id)
    else:
      print("ID or path to games.yml was invalid")
      sys.exit(1)

  def parse_game_metadata(self):
    for id in self._processor.game_ids:
      print(f"Parsing metadata of {id}...")

      response = self._downloader.get_parse(id)
      if response == None:
        continue
      
      tree = ElementTree.fromstring(response.content)
      
      game_id = tree.get("titleid")
      for xml in tree.find("tag").findall("package"):
        game_version = xml.get("version")
        game_size = convert_bytes_to_megabytes(xml.get("size"))
        game_sysver = xml.get("ps3_system_ver")
        game_url = xml.get("url")

        if xml.find("paramsfo") != None:
          game_name = xml.find("paramsfo").find("TITLE").text.replace("\n", " ")
      
      game = Game(game_id, game_name, game_url, game_size, game_sysver, game_version)
      self._processor.add_game(game)

class Downloader:
  def __init__(self, processor, app):
    self._processor = processor
    self._app = app
  
  def is_already_downloaded(self, id, filename):
    if self._app.get_platform("win32"):
      if file_exists(self._processor.game_updates_folder + "\\" + id + "\\" + filename) == True:
        return True
    elif self._app.get_platform("freebsd") or self._app.get_platform("linux") or self._app.get_platform("darwin"):
      if file_exists(self._processor.game_updates_folder + "/" + id + "/" + filename) == True:
        return True
    else:
      return False


  def get_parse(self, id):
    urllib3.disable_warnings()
    
    resp = requests.get(f"https://a0.ww.np.dl.playstation.net/tpl/np/{id}/{id}-ver.xml", verify=False)
    if resp.content == b'' or resp.status_code == 404:
      return None
    return resp
  
  def get_update(self):
    urllib3.disable_warnings()

    if folder_exists(self._processor.game_updates_folder) == False:
      print(f"Creating folder '{self._processor.game_updates_folder}' for game updates")
      path = Path(self._processor.game_updates_folder)
      path.mkdir(parents=True)
    
    downloads_left = 0

    for game in self._processor.game_list:
      self._processor.create_per_game_update_folder(game.id)

      filename = game.url.split("/")[-1]

      is_downloaded = self.is_already_downloaded(game.id, filename)
      if is_downloaded == True:
        continue
      else:
        print(f"Requesting game update download for: {game.name} ({game.id})")
        downloads_left += 1

        with requests.get(game.url, stream=True) as response:
          response.raise_for_status()

          update_length = int(response.headers.get("content-length", 0))
          if self._app.get_platform("win32"):
            with open(self._processor.game_updates_folder + "\\" + game.id + "\\" + filename, "wb") as f, tqdm(
              desc=filename,
              total=update_length,
              unit="iB",
              unit_scale=True,
              unit_divisor=1024,
            ) as bar:
              for chunk in response.iter_content(chunk_size=8192):
                size = f.write(chunk)
                bar.update(size)
          elif self._app.get_platform("freebsd") or self._app.get_platform("linux") or self._app.get_platform("darwin"):
            with open(self._processor.game_updates_folder + "/" + game.id + "/" + filename, "wb") as f, tqdm(
              desc=filename,
              total=update_length,
              unit="iB",
              unit_scale=True,
              unit_divisor=1024,
            ) as bar:
              for chunk in response.iter_content(chunk_size=8192):
                size = f.write(chunk)
                bar.update(size)

    if downloads_left == 0:
      print("Everything is already downloaded :)")
    else:
      print("Download(s) is/are complete")

# Functions
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

# Main
def main():
  app = App("rgudw", 1.0)
  game_processor = GameProcessor(app)
  game_processor.game_updates_folder = app.verify_platform()
  downloader = Downloader(game_processor, app)
  metadata_parser = MetadataParser(game_processor, downloader)

  if len(sys.argv) < 2:
    app.show_usage()
  elif len(sys.argv) >= 3:
    app.show_usage()
  else:
    metadata_parser.parse_game_ids(sys.argv[1])
    metadata_parser.parse_game_metadata()
    downloader.get_update()

if __name__ == "__main__":
  main()