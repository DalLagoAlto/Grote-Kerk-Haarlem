"""Haalt georeferentie-data op voor de Grote of Sint-Bavokerk (Grote Markt 22, Haarlem).

Bronnen: PDOK BGT (OGC API), PDOK BAG (OGC API), RCE rijksmonumenten (WFS).
Output: data/georeferencing_summary.json
"""
import json
import os
import sys

import requests
from pyproj import Transformer
from shapely.geometry import shape
from shapely.ops import unary_union

BAG_PAND = "0392100000037430"
RIJKSMONUMENT_NUMMER = 19264
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "georeferencing_summary.json")

BGT_PAND = "https://api.pdok.nl/kadaster/bgt/ogc/v1/collections/pand/items"
BAG_PAND_ITEMS = "https://api.pdok.nl/kadaster/bag/ogc/v2/collections/pand/items"
RCE_WFS = "https://services.rce.geovoorziening.nl/rce/wfs"
CRS_28992 = "http://www.opengis.net/def/crs/EPSG/0/28992"

RD2LL = Transformer.from_crs("EPSG:28992", "EPSG:4326", always_xy=True)


def bgt_pand(bag_pnd: str):
    r = requests.get(
        BGT_PAND,
        params={"f": "json", "limit": 10, "filter": f"bag_pnd='{bag_pnd}'", "crs": CRS_28992},
        timeout=60,
    )
    r.raise_for_status()
    return [shape(f["geometry"]) for f in r.json().get("features", [])
            if f["properties"].get("status") == "bestaand"]


def bag_pand():
    r = requests.get(
        BAG_PAND_ITEMS,
        params={"f": "json", "limit": 5, "bbox": "4.63683,52.38077,4.63783,52.38137",
                "filter": f"identificatie='{BAG_PAND}'"},
        timeout=60,
    )
    r.raise_for_status()
    feats = r.json().get("features", [])
    return feats[0]["properties"] if feats else {}


def monument_punt():
    r = requests.get(
        RCE_WFS,
        params={"request": "GetFeature", "service": "WFS", "version": "2.0.0",
                "typeNames": "rce:NationalListedMonumentPoints",
                "outputFormat": "application/json", "srsName": "EPSG:28992",
                "CQL_FILTER": f"rijksmonument_nummer={RIJKSMONUMENT_NUMMER}"},
        timeout=90,
    )
    r.raise_for_status()
    f = r.json()["features"][0]
    return f["properties"], f["geometry"]["coordinates"]


def main():
    kerk_panden = ["0392100000037430", "0392100000037432", "0392100000037433",
                   "0392100000037434", "0392100000037436", "0392100000037437",
                   "0392100000065734"]
    geoms = [g for pid in kerk_panden for g in bgt_pand(pid)]
    footprint = unary_union(geoms)
    b = footprint.bounds
    c = footprint.centroid
    lon, lat = RD2LL.transform(c.x, c.y)

    mon_props, mon_xy = monument_punt()
    mlon, mlat = RD2LL.transform(*mon_xy)

    summary = {
        "project": "Grote of Sint-Bavokerk (Grote Kerk), Grote Markt 22, 2011 RD Haarlem",
        "rijksmonument_nummer": RIJKSMONUMENT_NUMMER,
        "bag_pand_identificatie": BAG_PAND,
        "crs": {"primair": "EPSG:28992 (RD New)", "hoogte": "NAP (EPSG:7415)", "wgs84": "EPSG:4326"},
        "site_referentiepunt_rd": [round(c.x, 2), round(c.y, 2)],
        "site_referentiepunt_wgs84": [round(lat, 7), round(lon, 7)],
        "monument_punt_rd": [round(v, 2) for v in mon_xy],
        "monument_punt_wgs84": [round(mlat, 7), round(mlon, 7)],
        "kerkcomplex_footprint": {
            "area_m2": round(footprint.area, 1),
            "bbox_rd": [round(v, 2) for v in b],
            "centroid_rd": [round(c.x, 2), round(c.y, 2)],
            "centroid_wgs84": [round(lat, 7), round(lon, 7)],
            "geojson": json.loads(json.dumps(footprint.__geo_interface__)),
        },
        "bag_pand_props": bag_pand(),
        "monument_props": mon_props,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in summary.items() if k != "kerkcomplex_footprint"},
                     ensure_ascii=False, indent=1))
    print("footprint area m2:", summary["kerkcomplex_footprint"]["area_m2"])
    print("centroid RD:", summary["kerkcomplex_footprint"]["centroid_rd"])
    print("centroid WGS84:", summary["kerkcomplex_footprint"]["centroid_wgs84"])
    print("saved ->", os.path.normpath(OUT))


if __name__ == "__main__":
    sys.exit(main())
