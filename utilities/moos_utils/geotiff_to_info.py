from osgeo import osr, gdal
import sys

def main(filename, for_sim=False):
    # get the existing coordinate system
    ds = gdal.Open(filename)
    old_cs = osr.SpatialReference()
    old_cs.ImportFromWkt(ds.GetProjectionRef())

    # create the new coordinate system
    wgs84_wkt = """
    GEOGCS["WGS 84",
        DATUM["WGS_1984",
            SPHEROID["WGS 84",6378137,298.257223563,
                AUTHORITY["EPSG","7030"]],
            AUTHORITY["EPSG","6326"]],
        PRIMEM["Greenwich",0,
            AUTHORITY["EPSG","8901"]],
        UNIT["degree",0.01745329251994328,
            AUTHORITY["EPSG","9122"]],
        AUTHORITY["EPSG","4326"]]"""
    new_cs = osr.SpatialReference()
    new_cs.ImportFromWkt(wgs84_wkt)

    # create a transform object to convert between coordinate systems
    transform = osr.CoordinateTransformation(old_cs,new_cs)

    #get the point to transform, pixel (0,0) in this case
    width = ds.RasterXSize
    height = ds.RasterYSize
    gt = ds.GetGeoTransform()
    minx = gt[0]
    miny = gt[3] + width*gt[4] + height*gt[5]
    maxx = gt[0] + width*gt[1] + height*gt[2]
    maxy = gt[3]

    #get the coordinates in lat long
    coords = list()
    # Northwest
    coords.append(transform.TransformPoint(minx,maxy))
    # Northeast
    coords.append(transform.TransformPoint(maxx,maxy))
    # Southwest
    coords.append(transform.TransformPoint(minx,miny))
    # Southeast
    coords.append(transform.TransformPoint(maxx,miny))

    # print(coords)

    north = (coords[0][1] + coords[1][1]) / 2
    south = (coords[2][1] + coords[3][1]) / 2
    west = (coords[0][0] + coords[2][0]) / 2
    east = (coords[1][0] + coords[3][0]) / 2

    print("lat_north = {0:.7f}".format(north))
    print("lat_south = {0:.7f}".format(south))
    print("lon_west = {0:.7f}".format(west))
    print("lon_east = {0:.7f}".format(east))
    if for_sim:
        print("datum_lat = {0:.7f}".format(south))
        print("datum_lon = {0:.7f}".format(west))
        print("//x_offset = {0:.3f}".format(minx))
        print("//y_offset = {0:.3f}".format(miny))
    else:
        print("datum_lat = {0:.7f}".format((north + south) / 2))
        print("datum_lon = {0:.7f}".format((east + west) / 2))

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python geotiff_to_info.py [--for_sim] filename.tif")
    else:
        if len(sys.argv) > 2:
            main(sys.argv[2], True)
        else:
            main(sys.argv[1])
