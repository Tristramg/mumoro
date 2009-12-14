import array
import math
import zipfile
import os.path
import urllib

def filename(lat, lon):
    if lat > 0 :
        filename = "N%02d" % math.trunc(lat)
    else:
        filename = "S%02d" % -math.trunc(lat - 1)
    if lon > 0 :
        filename += "E%03d.hgt" % math.trunc(lon)
    else:
        filename += "W%03d.hgt" % -math.trunc(lon - 1)
    return  filename


class Tile:
    nb_coords = 1201;
    def __init__(self, lat, lon):
        zf = zipfile.ZipFile(filename(lat, lon) + ".zip")
        self.data = array.array("h", zf.read(filename(lat, lon)))
        self.data.byteswap()

    def altitude(self, lat, lon):
        lon_dec = abs(lon) - math.trunc(abs(lon))
        lat_dec = abs(lat) - math.trunc(abs(lat))
        
        if lon > 0 :
            lon_idx = math.trunc(lon_dec * self.nb_coords)
        else:
            lon_idx = math.trunc((1 - lon_dec) * self.nb_coords -1)
        if lat > 0 :
            lat_idx = math.trunc((1 - lat_dec) * self.nb_coords - 1)
        else:
            lat_idx = math.trunc(lat_dec * self.nb_coords)

        return self.data[lat_idx * self.nb_coords + lon_idx]

class ElevationData:
    def __init__(self, continent):
        if continent not in ["Africa", "Australia", "Eurasia", "Islands", "North_America", "South_America"]:
            print "Error: unknow continent %s." % continent
            raise Exception
        self.tiles = {}
        self.continent = continent


    def altitude(self, lat, lon):
        fn = filename(lat, lon)
        if not self.tiles.has_key(fn):
            if not os.path.exists(fn + ".zip"):
#                url = "ftp://e0srp01u.ecs.nasa.gov/srtm/version2/SRTM3/%s/%s.zip" % (self.continent, fn)
                url = "http://dds.cr.usgs.gov/srtm/version2_1/SRTM3/%s/%s.zip" % (self.continent, fn)
                print "Tile not in cache. Downloading %s " %url
                urllib.urlretrieve(url, fn + ".zip")
                print "    Done!"
            self.tiles[fn] = Tile(lat, lon)
        return self.tiles[fn].altitude(lat, lon)
