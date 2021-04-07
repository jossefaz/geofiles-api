import os
from ..convertors.Convertor import Convertor
import json
from pathlib import Path
import subprocess

class DwgConvertor(Convertor):

    def __init__(self, path):
        self.path = path

    def to_shp(self):
        pass

    def to_dwg(self):
        pass

    def to_geojson(self):
        json_tmp = os.path.join("app/uploads", "temp.json")
        try:
            return_code = subprocess.call(["dwgread", self.path, "-O", "GeoJSON", "-o", json_tmp])
            if not return_code == 0 or not Path(json_tmp).exists():
                return False
            try:
                with open(json_tmp, 'r') as fp:
                    json_dict = json.loads(fp.read())
                    if "features" not in json_dict:
                        print("invalid GeoJSON")
                        return False
                    try:
                        json_dict["features"] = [feature for feature in json_dict["features"]
                                                 if feature["geometry"] is not None]
                        return json.dumps(json_dict)
                    except KeyError as e:
                        print(e)
                        return False
            except Exception as e:
                print(e)
                return False
        except Exception as e:
            print(e)
            return False
        finally:
            if Path(json_tmp).exists():
                Path(json_tmp).unlink()

    def to_csv(self):
        pass