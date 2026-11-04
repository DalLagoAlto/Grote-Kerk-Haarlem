"""Valideert een IFC4-bestand: schema, georeferentie, entiteiten, geometrie-bbox vs BGT."""
import json
import os
import sys
from collections import Counter

import ifcopenshell
import ifcopenshell.geom
from shapely.geometry import shape

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
SUMMARY = os.path.join(ROOT, "data", "georeferencing_summary.json")
REPORT = os.path.join(ROOT, "docs", "validatie.md")


def main(ifc_path):
    with open(SUMMARY) as fh:
        summary = json.load(fh)
    x0, y0 = summary["site_referentiepunt_rd"]
    lat, lon = summary["site_referentiepunt_wgs84"]
    bgt = summary["kerkcomplex_footprint"]

    f = ifcopenshell.open(ifc_path)
    lines = []
    lines.append("# Validatierapport — %s" % os.path.basename(ifc_path))
    lines.append("")
    lines.append("- IFC-schema: `%s`" % f.schema)
    ok_schema = f.schema == "IFC4"

    counts = Counter(e.is_a() for e in f)
    lines.append("- Entiteiten totaal: %d" % sum(counts.values()))
    for t in ("IfcProject", "IfcSite", "IfcBuilding", "IfcBuildingStorey", "IfcWall",
              "IfcSlab", "IfcRoof", "IfcBuildingElementProxy", "IfcProjectedCRS",
              "IfcMapConversion", "IfcPropertySet"):
        lines.append("  - %s: %d" % (t, counts.get(t, 0)))

    mcs = f.by_type("IfcMapConversion")
    if mcs:
        mc = mcs[0]
        crs_name = mc.TargetCRS.Name if mc.TargetCRS else "?"
        lines.append("- IfcMapConversion: TargetCRS=`%s`, Eastings=%.2f, Northings=%.2f, "
                     "OrthogonalHeight=%.2f, rot=(%.3f,%.3f), scale=%.3f"
                     % (crs_name, mc.Eastings, mc.Northings, mc.OrthogonalHeight,
                        mc.XAxisAbscissa, mc.XAxisOrdinate, mc.Scale))
        ok_map = ("28992" in str(crs_name)) and abs(mc.Eastings - x0) < 0.01 and abs(mc.Northings - y0) < 0.01
    else:
        ok_map = False
        lines.append("- IfcMapConversion: **ONTBREEKT**")

    sites = f.by_type("IfcSite")
    ok_site = False
    if sites:
        s = sites[0]
        def to_dec(dms):
            return dms[0] + dms[1] / 60 + dms[2] / 3600 + (dms[3] if len(dms) > 3 else 0) / 3.6e9
        slat = to_dec(s.RefLatitude) if s.RefLatitude else None
        slon = to_dec(s.RefLongitude) if s.RefLongitude else None
        lines.append("- IfcSite: RefLatitude=%.7f RefLongitude=%.7f RefElevation=%.2f (verwacht WGS84 %.7f / %.7f)"
                     % (slat or -1, slon or -1, s.RefElevation or 0, lat, lon))
        ok_site = slat is not None and abs(slat - lat) < 1e-5 and abs(slon - lon) < 1e-5

    settings = ifcopenshell.geom.settings()
    n_verts = 0
    products = [p for p in f.by_type("IfcProduct") if p.is_a("IfcElement") and p.Representation]
    geom_ok = True
    for p in products:
        try:
            sh = ifcopenshell.geom.create_shape(settings, p)
            n_verts += len(sh.geometry.verts)
        except Exception as exc:
            geom_ok = False
            lines.append("- geometrie FOUT bij %s: %s" % (p.Name, exc))
    lines.append("- Geometrie: %d elementen, %d vertices, %s" % (len(products), n_verts, "OK" if geom_ok else "FOUT"))

    local_pts = []
    for c in f.by_type("IfcCartesianPointList2D"):
        local_pts.extend(c.CoordList)
    if local_pts:
        xs = [p[0] for p in local_pts]
        ys = [p[1] for p in local_pts]
        rd_bbox = (min(xs) + x0, min(ys) + y0, max(xs) + x0, max(ys) + y0)
        b = bgt["bbox_rd"]
        lines.append("- BBox model in RD: X %.2f..%.2f Y %.2f..%.2f" % (rd_bbox[0], rd_bbox[2], rd_bbox[1], rd_bbox[3]))
        lines.append("- BBox BGT : X %.2f..%.2f Y %.2f..%.2f" % (b[0], b[2], b[1], b[3]))
        ok_bbox = abs(rd_bbox[0] - b[0]) < 0.05 and abs(rd_bbox[2] - b[2]) < 0.05 \
            and abs(rd_bbox[1] - b[1]) < 0.05 and abs(rd_bbox[3] - b[3]) < 0.05
    else:
        ok_bbox = False

    lines.append("")
    lines.append("## Resultaat")
    lines.append("- schema IFC4: %s" % ("OK" if ok_schema else "FOUT"))
    lines.append("- georeferentie (EPSG:28992 + map conversion op site-ref): %s" % ("OK" if ok_map else "FOUT"))
    lines.append("- IfcSite RefLat/Lon = WGS84 site-ref: %s" % ("OK" if ok_site else "FOUT"))
    lines.append("- geometrie leesbaar: %s" % ("OK" if geom_ok else "FOUT"))
    lines.append("- bbox model == BGT-voetafdruk: %s" % ("OK" if ok_bbox else "FOUT"))
    verdict = all([ok_schema, ok_map, ok_site, geom_ok, ok_bbox])
    lines.append("- **TOTAAL: %s**" % ("GESLAAGD" if verdict else "NIET GESLAAGD"))

    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0 if verdict else 1


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "ifc", "Grote-Kerk-Haarlem_v0_massing.ifc")
    sys.exit(main(path))
