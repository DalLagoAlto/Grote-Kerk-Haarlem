"""IFC4 v1: kruisvormige wanden/daken/toren/deuren uit de restauratietekeningen, gegeorefereerd."""
import json
import math
import os
import sys
import time

import ifcopenshell
import ifcopenshell.api.pset
import ifcopenshell.guid
from ifcopenshell.api.unit import add_si_unit, assign_unit
from shapely.geometry import shape

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
SUMMARY = os.path.join(ROOT, "data", "georeferencing_summary.json")
OUT = os.path.join(ROOT, "ifc", "Grote-Kerk-Haarlem_v1.ifc")

WALL_T = 1.0
GOOT = 21.0
NOK = 29.0
TOREN_TOP = 78.0
TOREN_B = 7.37
DOOR_H = 3.0

LENGTH_X = 118.0
NAVE_W = 24.0
CHOIR_LEN = 44.0
TRANSEPT_W = 36.0


def dms(dec):
    d = int(abs(dec))
    m = int((abs(dec) - d) * 60)
    s = (abs(dec) - d - m / 60) * 3600
    return [d, m, int(s), int(round((s - int(s)) * 1e6))]


def axis3d(f, loc=(0.0, 0.0, 0.0), axis=(0.0, 0.0, 1.0), ref=(1.0, 0.0, 0.0)):
    return f.create_entity(
        "IfcAxis2Placement3D",
        Location=f.create_entity("IfcCartesianPoint", Coordinates=list(loc)),
        Axis=f.create_entity("IfcDirection", DirectionRatios=list(axis)),
        RefDirection=f.create_entity("IfcDirection", DirectionRatios=list(ref)),
    )


def local_placement(f, rel_to, loc=(0.0, 0.0, 0.0)):
    return f.create_entity("IfcLocalPlacement", PlacementRelTo=rel_to, RelativePlacement=axis3d(f, loc))


def rect_solid(f, x0, y0, z0, dx, dy, dz):
    pts = [[x0, y0], [x0 + dx, y0], [x0 + dx, y0 + dy], [x0, y0 + dy], [x0, y0]]
    curve = f.create_entity(
        "IfcIndexedPolyCurve",
        Points=f.create_entity("IfcCartesianPointList2D", CoordList=pts),
    )
    prof = f.create_entity("IfcArbitraryClosedProfileDef", ProfileType="AREA", OuterCurve=curve)
    return f.create_entity(
        "IfcExtrudedAreaSolid",
        SweptArea=prof,
        Position=axis3d(f, (0.0, 0.0, z0)),
        ExtrudedDirection=f.create_entity("IfcDirection", DirectionRatios=[0.0, 0.0, 1.0]),
        Depth=dz,
    ), dx, dy


def gable_solid(f, x0, y0, z_eave, ridge_z, half_w, length, along_x, loc_z=0.0):
    if along_x:
        axis = (1.0, 0.0, 0.0)
        ref = (0.0, 0.0, 1.0)
        pts = [[z_eave, half_w], [ridge_z, 0.0], [z_eave, -half_w], [z_eave, half_w]]
        loc = (x0, y0, loc_z)
    else:
        axis = (0.0, 1.0, 0.0)
        ref = (0.0, 0.0, 1.0)
        pts = [[z_eave, half_w], [ridge_z, 0.0], [z_eave, -half_w], [z_eave, half_w]]
        loc = (x0, y0, loc_z)
    curve = f.create_entity(
        "IfcIndexedPolyCurve",
        Points=f.create_entity("IfcCartesianPointList2D", CoordList=pts),
    )
    prof = f.create_entity("IfcArbitraryClosedProfileDef", ProfileType="AREA", OuterCurve=curve)
    return f.create_entity(
        "IfcExtrudedAreaSolid",
        SweptArea=prof,
        Position=axis3d(f, loc, axis=axis, ref=ref),
        ExtrudedDirection=f.create_entity("IfcDirection", DirectionRatios=list(axis)),
        Depth=length,
    )


def product(f, ctx, ifc_type, name, rel_to, solid, predefined=None, objtype=None):
    kwargs = {
        "GlobalId": ifcopenshell.guid.new(),
        "Name": name,
        "ObjectPlacement": local_placement(f, rel_to),
        "Representation": f.create_entity(
            "IfcProductDefinitionShape",
            Representations=[
                f.create_entity(
                    "IfcShapeRepresentation",
                    ContextOfItems=ctx,
                    RepresentationIdentifier="Body",
                    RepresentationType="SweptSolid",
                    Items=[solid],
                )
            ],
        ),
    }
    if predefined:
        kwargs["PredefinedType"] = predefined
    if objtype:
        kwargs["ObjectType"] = objtype
    return f.create_entity(ifc_type, **kwargs)


def add_pset(f, product_, name, props):
    pset = ifcopenshell.api.run("pset.add_pset", f, product=product_, name=name)
    ifcopenshell.api.run("pset.edit_pset", f, pset=pset, properties=props)
    return pset


def main():
    with open(SUMMARY) as fh:
        summary = json.load(fh)
    x0, y0 = summary["site_referentiepunt_rd"]
    lat, lon = summary["site_referentiepunt_wgs84"]
    fp = shape(summary["kerkcomplex_footprint"]["geojson"])
    if fp.geom_type == "MultiPolygon":
        fp = max(fp.geoms, key=lambda g: g.area)
    b = fp.bounds
    x_min, x_max = b[0] - x0, b[2] - x0
    y_min, y_max = b[1] - y0, b[3] - y0

    west = x_min + 0.5
    east = west + LENGTH_X
    y_c = (y_min + y_max) / 2.0
    nave_y0, nave_y1 = y_c - NAVE_W / 2, y_c + NAVE_W / 2
    choir_x0 = west + (LENGTH_X - CHOIR_LEN)
    trans_x_c = west + (LENGTH_X - CHOIR_LEN) - TRANSEPT_W / 2
    trans_y0, trans_y1 = y_min + 0.5, y_max - 0.5

    f = ifcopenshell.file(schema="IFC4")
    ts = int(time.time())
    person = f.create_entity("IfcPerson", FamilyName="Vibe", GivenName="Code")
    org = f.create_entity("IfcOrganization", Name="Mistral AI — Vibe Code")
    app = f.create_entity("IfcApplication", ApplicationDeveloper=org, Version="1.0",
                          ApplicationFullName="Vibe Code", ApplicationIdentifier="vibe")
    oh = f.create_entity("IfcOwnerHistory", OwningUser=person, OwningApplication=app,
                         State="READWRITE", ChangeAction="ADDED", CreationDate=ts)

    ctx = f.create_entity(
        "IfcGeometricRepresentationContext", ContextIdentifier=None, ContextType="Model",
        CoordinateSpaceDimension=3, Precision=1e-5, WorldCoordinateSystem=axis3d(f),
        TrueNorth=f.create_entity("IfcDirection", DirectionRatios=[0.0, 1.0]),
    )
    project = f.create_entity(
        "IfcProject", GlobalId=ifcopenshell.guid.new(), OwnerHistory=oh,
        Name="Grote Kerk Haarlem — IFC4 v1",
        Description="IFC4-model Grote of Sint-Bavokerk, Grote Markt 22, Haarlem (rijksmonument 19264). Geometrie uit restauratietekeningen (42 bladen); positie uit BGT. RD New EPSG:28992 + NAP.",
        RepresentationContexts=[ctx],
    )
    metre = add_si_unit(f, "LENGTHUNIT")
    assign_unit(f, units=[metre, add_si_unit(f, "PLANEANGLEUNIT"), add_si_unit(f, "SOLIDANGLEUNIT")])

    proj_crs = f.create_entity(
        "IfcProjectedCRS", Name="EPSG:28992",
        Description="RD New — Amersfoort / Bessel 1841, dubbele stereografische projectie",
        GeodeticDatum="EPSG:4289", VerticalDatum="EPSG:5709",
        MapProjection="Double Stereographic", MapZone="", MapUnit=metre,
    )
    f.create_entity(
        "IfcMapConversion", SourceCRS=ctx, TargetCRS=proj_crs,
        Eastings=x0, Northings=y0, OrthogonalHeight=0.0,
        XAxisAbscissa=1.0, XAxisOrdinate=0.0, Scale=1.0,
    )

    address = f.create_entity(
        "IfcPostalAddress", AddressLines=["Grote Markt 22"], Town="Haarlem",
        Region="Noord-Holland", PostalCode="2011 RD", Country="Nederland",
    )
    site = f.create_entity(
        "IfcSite", GlobalId=ifcopenshell.guid.new(), OwnerHistory=oh, Name="Terrein Grote Kerk",
        ObjectPlacement=local_placement(f, None), LongName="Grote Markt 22, 2011 RD Haarlem",
        CompositionType="ELEMENT", RefLatitude=dms(lat), RefLongitude=dms(lon),
        RefElevation=0.0, SiteAddress=address,
    )
    f.create_entity("IfcRelAggregates", GlobalId=ifcopenshell.guid.new(), OwnerHistory=oh,
                    RelatingObject=project, RelatedObjects=[site])
    building = f.create_entity(
        "IfcBuilding", GlobalId=ifcopenshell.guid.new(), OwnerHistory=oh,
        Name="Grote of Sint-Bavokerk", ObjectPlacement=local_placement(f, site.ObjectPlacement),
        ElevationOfRefHeight=0.0,
    )
    f.create_entity("IfcRelAggregates", GlobalId=ifcopenshell.guid.new(), OwnerHistory=oh,
                    RelatingObject=site, RelatedObjects=[building])
    storey = f.create_entity(
        "IfcBuildingStorey", GlobalId=ifcopenshell.guid.new(), OwnerHistory=oh, Name="Begane grond",
        ObjectPlacement=local_placement(f, building.ObjectPlacement), Elevation=0.0,
    )
    f.create_entity("IfcRelAggregates", GlobalId=ifcopenshell.guid.new(), OwnerHistory=oh,
                    RelatingObject=building, RelatedObjects=[storey])

    elements = []

    slab_pts = [(x - x0, y - y0) for x, y in fp.exterior.coords]
    curve = f.create_entity("IfcIndexedPolyCurve",
                            Points=f.create_entity("IfcCartesianPointList2D", CoordList=[[p[0], p[1]] for p in slab_pts]))
    slab_prof = f.create_entity("IfcArbitraryClosedProfileDef", ProfileType="AREA", OuterCurve=curve)
    slab_solid = f.create_entity(
        "IfcExtrudedAreaSolid", SweptArea=slab_prof, Position=axis3d(f, (0.0, 0.0, -0.3)),
        ExtrudedDirection=f.create_entity("IfcDirection", DirectionRatios=[0.0, 0.0, 1.0]), Depth=0.3,
    )
    elements.append(product(f, ctx, "IfcSlab", "Terreinplaat (BGT-voetafdruk)", storey.ObjectPlacement, slab_solid, predefined="FLOOR"))

    def wall(name, x_a, y_a, x_b, y_b, h=GOOT):
        dx = abs(x_b - x_a) or WALL_T
        dy = abs(y_b - y_a) or WALL_T
        solid, _, _ = rect_solid(f, min(x_a, x_b), min(y_a, y_b), 0.0, dx, dy, h)
        return product(f, ctx, "IfcWall", name, storey.ObjectPlacement, solid, predefined="SOLIDWALL")

    blocks = [
        ("schip", west, nave_y0, choir_x0, nave_y1),
        ("koor", choir_x0, nave_y0, east, nave_y1),
        ("transept", trans_x_c - TRANSEPT_W / 2, trans_y0, trans_x_c + TRANSEPT_W / 2, trans_y1),
    ]
    for bname, bx0, by0, bx1, by1 in blocks:
        elements.append(wall(f"Buitenmuur {bname} noord", bx0, by1 - WALL_T, bx1, by1))
        elements.append(wall(f"Buitenmuur {bname} zuid", bx0, by0, bx1, by0 + WALL_T))
        elements.append(wall(f"Buitenmuur {bname} west", bx0, by0, bx0 + WALL_T, by1))
        elements.append(wall(f"Buitenmuur {bname} oost", bx1 - WALL_T, by0, bx1, by1))

    tw_x0 = trans_x_c - TOREN_B / 2
    tw_x1 = trans_x_c + TOREN_B / 2
    tw_y0 = y_c - TOREN_B / 2
    tw_y1 = y_c + TOREN_B / 2
    for nm, a, b, c, d in [
        ("noord", tw_x0, tw_y1 - WALL_T, tw_x1, tw_y1),
        ("zuid", tw_x0, tw_y0, tw_x1, tw_y0 + WALL_T),
        ("west", tw_x0, tw_y0, tw_x0 + WALL_T, tw_y1),
        ("oost", tw_x1 - WALL_T, tw_y0, tw_x1, tw_y1),
    ]:
        elements.append(wall(f"Vieringtoren {nm}", a, b, c, d, h=GOOT))
    toren_solid, _, _ = rect_solid(f, tw_x0, tw_y0, GOOT, TOREN_B, TOREN_B, TOREN_TOP - GOOT)
    elements.append(product(f, ctx, "IfcBuildingElementProxy", "Vieringtoren spits (indicatief, tot +78 m)",
                            storey.ObjectPlacement, toren_solid, predefined="USERDEFINED",
                            objtype="Toren spits 29-78 m (vierkant, indicatief)"))

    def roof(name, x_a, y_a, half_w, length, along_x):
        solid = gable_solid(f, x_a, y_a, GOOT, NOK, half_w, length, along_x)
        return product(f, ctx, "IfcRoof", name, storey.ObjectPlacement, solid, predefined="GABLE_ROOF")

    elements.append(roof("Dak schip+koor (nok +29 m)", west, y_c, NAVE_W / 2, LENGTH_X, True))
    elements.append(roof("Dak transept (nok +29 m)", trans_x_c, trans_y0, TRANSEPT_W / 2, trans_y1 - trans_y0, False))

    def door(name, x_a, y_a, w, wall_along_y):
        if wall_along_y:
            solid, _, _ = rect_solid(f, x_a, y_a - w / 2, 0.0, WALL_T, w, DOOR_H)
        else:
            solid, _, _ = rect_solid(f, x_a - w / 2, y_a, 0.0, w, WALL_T, DOOR_H)
        return product(f, ctx, "IfcDoor", name, storey.ObjectPlacement, solid, predefined="DOOR")

    elements.append(door("Hoofdingang west (4.00 m)", west, y_c, 4.0, True))
    elements.append(door("Ingang transept noord (3.00 m)", trans_x_c, trans_y1 - WALL_T, 3.0, False))
    elements.append(door("Ingang transept zuid (3.00 m)", trans_x_c, trans_y0, 3.0, False))
    elements.append(door("Ingang koor oost (3.00 m)", east - WALL_T, y_c, 3.0, True))

    f.create_entity(
        "IfcRelContainedInSpatialStructure", GlobalId=ifcopenshell.guid.new(), OwnerHistory=oh,
        RelatedElements=elements, RelatingStructure=storey,
    )

    mat = f.create_entity("IfcMaterial", Name="Baksteen (indicatief)")
    f.create_entity("IfcRelAssociatesMaterial", GlobalId=ifcopenshell.guid.new(), OwnerHistory=oh,
                    RelatedObjects=elements, RelatingMaterial=mat)

    mon = summary.get("monument_props", {})
    add_pset(f, building, "Pset_Rijksmonument", {
        "Monumentnummer": str(summary["rijksmonument_nummer"]),
        "RijksmonumentURL": mon.get("rijksmonumenturl", ""),
        "Hoofdcategorie": mon.get("hoofdcategorie", ""),
        "Subcategorie": mon.get("subcategorie", ""),
    })
    bag = summary.get("bag_pand_props", {})
    add_pset(f, building, "Pset_BAG", {
        "PandIdentificatie": summary["bag_pand_identificatie"],
        "Bouwjaar": int(bag.get("bouwjaar", 1400)),
        "Gebruiksdoel": str(bag.get("gebruiksdoel", "bijeenkomstfunctie")),
    })
    add_pset(f, building, "Pset_MatenUitTekeningen", {
        "TotaleLengte_m": LENGTH_X, "SchipBreedte_m": NAVE_W, "KoorLengte_m": CHOIR_LEN,
        "TranseptBreedte_m": TRANSEPT_W, "Wanddikte_m": WALL_T, "Goothoogte_m": GOOT,
        "Nokhoogte_m": NOK, "TorenTop_m": TOREN_TOP, "TorenBreedte_m": TOREN_B,
        "Bron": "plattegrond blad 1 (1:100); gevels B81/+21/+29; doorsnedes",
    })
    add_pset(f, site, "Pset_Georeferentie", {
        "CRS": "EPSG:28992 (RD New) + NAP (EPSG:7415); secundair WGS84 EPSG:4326",
        "SiteRefRD_X": float(x0), "SiteRefRD_Y": float(y0),
        "SiteRefWGS84_Lat": float(lat), "SiteRefWGS84_Lon": float(lon),
        "Bron": "BGT pand via PDOK OGC API; RCE rijksmonument 19264",
    })

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    f.write(OUT)
    from collections import Counter
    counts = Counter(e.is_a() for e in f.by_type("IfcElement"))
    print("geschreven:", OUT)
    print("schema:", f.schema, "| elementen:", dict(counts))
    print("site ref RD: X=%.2f Y=%.2f | WGS84 %.7f / %.7f" % (x0, y0, lat, lon))


if __name__ == "__main__":
    sys.exit(main())
