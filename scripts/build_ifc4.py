"""Genereert het IFC4-model van de Grote Kerk Haarlem (v0: massing uit BGT-voetafdruk)."""
import json
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
OUT = os.path.join(ROOT, "ifc", "Grote-Kerk-Haarlem_v0_massing.ifc")
MASSING_HEIGHT = 20.0
SLAB_DEPTH = 0.3


def dms(dec):
    d = int(abs(dec))
    m = int((abs(dec) - d) * 60)
    s = (abs(dec) - d - m / 60) * 3600
    return [d, m, int(s), int(round((s - int(s)) * 1e6))]


def axis3d(f, loc=(0.0, 0.0, 0.0)):
    return f.create_entity(
        "IfcAxis2Placement3D",
        Location=f.create_entity("IfcCartesianPoint", Coordinates=list(loc)),
        Axis=f.create_entity("IfcDirection", DirectionRatios=[0.0, 0.0, 1.0]),
        RefDirection=f.create_entity("IfcDirection", DirectionRatios=[1.0, 0.0, 0.0]),
    )


def local_placement(f, rel_to, loc=(0.0, 0.0, 0.0)):
    return f.create_entity("IfcLocalPlacement", PlacementRelTo=rel_to, RelativePlacement=axis3d(f, loc))


def profile_from_polygon(f, exterior_local):
    pts = list(exterior_local)
    if pts[0] != pts[-1]:
        pts.append(pts[0])
    curve = f.create_entity(
        "IfcIndexedPolyCurve",
        Points=f.create_entity("IfcCartesianPointList2D", CoordList=[[p[0], p[1]] for p in pts]),
    )
    return f.create_entity("IfcArbitraryClosedProfileDef", ProfileType="AREA", OuterCurve=curve)


def extruded_solid(f, profile, z0, depth):
    return f.create_entity(
        "IfcExtrudedAreaSolid",
        SweptArea=profile,
        Position=axis3d(f, (0.0, 0.0, z0)),
        ExtrudedDirection=f.create_entity("IfcDirection", DirectionRatios=[0.0, 0.0, 1.0]),
        Depth=depth,
    )


def product_representation(f, ctx, items):
    return f.create_entity(
        "IfcProductDefinitionShape",
        Representations=[
            f.create_entity(
                "IfcShapeRepresentation",
                ContextOfItems=ctx,
                RepresentationIdentifier="Body",
                RepresentationType="SweptSolid",
                Items=items,
            )
        ],
    )


def add_pset(f, product, name, props):
    pset = ifcopenshell.api.run("pset.add_pset", f, product=product, name=name)
    ifcopenshell.api.run("pset.edit_pset", f, pset=pset, properties=props)
    return pset


def main():
    with open(SUMMARY) as fh:
        summary = json.load(fh)

    x0, y0 = summary["site_referentiepunt_rd"]
    lat, lon = summary["site_referentiepunt_wgs84"]
    fp = summary["kerkcomplex_footprint"]["geojson"]
    geom = shape(fp)
    if geom.geom_type == "MultiPolygon":
        geom = max(geom.geoms, key=lambda g: g.area)
    exterior = [(x - x0, y - y0) for x, y in geom.exterior.coords]

    f = ifcopenshell.file(schema="IFC4")
    ts = int(time.time())
    person = f.create_entity("IfcPerson", FamilyName="Vibe", GivenName="Code")
    org = f.create_entity("IfcOrganization", Name="Mistral AI — Vibe Code")
    app = f.create_entity(
        "IfcApplication", ApplicationDeveloper=org, Version="1.0",
        ApplicationFullName="Vibe Code", ApplicationIdentifier="vibe",
    )
    oh = f.create_entity(
        "IfcOwnerHistory", OwningUser=person, OwningApplication=app,
        State="READWRITE", ChangeAction="ADDED", CreationDate=ts,
    )

    ctx = f.create_entity(
        "IfcGeometricRepresentationContext",
        ContextIdentifier=None,
        ContextType="Model",
        CoordinateSpaceDimension=3,
        Precision=1e-5,
        WorldCoordinateSystem=axis3d(f),
        TrueNorth=f.create_entity("IfcDirection", DirectionRatios=[0.0, 1.0]),
    )

    project = f.create_entity(
        "IfcProject",
        GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=oh,
        Name="Grote Kerk Haarlem — IFC4",
        Description="IFC4-model van de Grote of Sint-Bavokerk, Grote Markt 22, Haarlem (rijksmonument 19264), gegeorefereerd in RD New (EPSG:28992) + NAP.",
        RepresentationContexts=[ctx],
    )
    metre = add_si_unit(f, "LENGTHUNIT")
    assign_unit(f, units=[metre, add_si_unit(f, "PLANEANGLEUNIT"), add_si_unit(f, "SOLIDANGLEUNIT")])

    proj_crs = f.create_entity(
        "IfcProjectedCRS",
        Name="EPSG:28992",
        Description="RD New — Amersfoort / Bessel 1841, dubbele stereografische projectie",
        GeodeticDatum="EPSG:4289",
        VerticalDatum="EPSG:5709",
        MapProjection="Double Stereographic",
        MapZone="",
        MapUnit=metre,
    )
    f.create_entity(
        "IfcMapConversion",
        SourceCRS=ctx,
        TargetCRS=proj_crs,
        Eastings=x0,
        Northings=y0,
        OrthogonalHeight=0.0,
        XAxisAbscissa=1.0,
        XAxisOrdinate=0.0,
        Scale=1.0,
    )

    address = f.create_entity(
        "IfcPostalAddress",
        AddressLines=["Grote Markt 22"],
        Town="Haarlem",
        Region="Noord-Holland",
        PostalCode="2011 RD",
        Country="Nederland",
    )
    site = f.create_entity(
        "IfcSite",
        GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=oh,
        Name="Terrein Grote Kerk",
        ObjectPlacement=local_placement(f, None),
        LongName="Grote Markt 22, 2011 RD Haarlem",
        CompositionType="ELEMENT",
        RefLatitude=dms(lat),
        RefLongitude=dms(lon),
        RefElevation=0.0,
        SiteAddress=address,
    )
    f.create_entity(
        "IfcRelAggregates", GlobalId=ifcopenshell.guid.new(), OwnerHistory=oh,
        RelatingObject=project, RelatedObjects=[site],
    )

    building = f.create_entity(
        "IfcBuilding",
        GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=oh,
        Name="Grote of Sint-Bavokerk",
        ObjectPlacement=local_placement(f, site.ObjectPlacement),
        ElevationOfRefHeight=0.0,
    )
    f.create_entity(
        "IfcRelAggregates", GlobalId=ifcopenshell.guid.new(), OwnerHistory=oh,
        RelatingObject=site, RelatedObjects=[building],
    )

    storey = f.create_entity(
        "IfcBuildingStorey",
        GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=oh,
        Name="Begane grond",
        ObjectPlacement=local_placement(f, building.ObjectPlacement),
        Elevation=0.0,
    )
    f.create_entity(
        "IfcRelAggregates", GlobalId=ifcopenshell.guid.new(), OwnerHistory=oh,
        RelatingObject=building, RelatedObjects=[storey],
    )

    profile = profile_from_polygon(f, exterior)

    slab = f.create_entity(
        "IfcSlab",
        GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=oh,
        Name="Terreinplaat (BGT-voetafdruk)",
        ObjectPlacement=local_placement(f, storey.ObjectPlacement),
        PredefinedType="FLOOR",
        Representation=product_representation(f, ctx, [extruded_solid(f, profile, -SLAB_DEPTH, SLAB_DEPTH)]),
    )
    massing = f.create_entity(
        "IfcBuildingElementProxy",
        GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=oh,
        Name="Massing v0 — BGT-voetafdruk",
        ObjectType="Massing (provisorisch, hoogte %.1f m)" % MASSING_HEIGHT,
        ObjectPlacement=local_placement(f, storey.ObjectPlacement),
        PredefinedType="USERDEFINED",
        Representation=product_representation(f, ctx, [extruded_solid(f, profile, 0.0, MASSING_HEIGHT)]),
    )
    f.create_entity(
        "IfcRelContainedInSpatialStructure",
        GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=oh,
        RelatedElements=[slab, massing],
        RelatingStructure=storey,
    )

    mat = f.create_entity("IfcMaterial", Name="Baksteen (indicatief)")
    f.create_entity(
        "IfcRelAssociatesMaterial", GlobalId=ifcopenshell.guid.new(), OwnerHistory=oh,
        RelatedObjects=[massing], RelatingMaterial=mat,
    )

    mon = summary.get("monument_props", {})
    add_pset(f, building, "Pset_Rijksmonument", {
        "Monumentnummer": str(summary["rijksmonument_nummer"]),
        "RijksmonumentURL": mon.get("rijksmonumenturl", ""),
        "AardMonument": mon.get("aard_monument", ""),
        "Hoofdcategorie": mon.get("hoofdcategorie", ""),
        "Subcategorie": mon.get("subcategorie", ""),
    })
    bag = summary.get("bag_pand_props", {})
    add_pset(f, building, "Pset_BAG", {
        "PandIdentificatie": summary["bag_pand_identificatie"],
        "Bouwjaar": int(bag.get("bouwjaar", 1400)),
        "Gebruiksdoel": str(bag.get("gebruiksdoel", "bijeenkomstfunctie")),
        "Status": str(bag.get("status", "Pand in gebruik")),
    })
    add_pset(f, site, "Pset_Georeferentie", {
        "CRS": "EPSG:28992 (RD New) + NAP (EPSG:7415); secundair WGS84 EPSG:4326",
        "SiteRefRD_X": float(x0),
        "SiteRefRD_Y": float(y0),
        "SiteRefWGS84_Lat": float(lat),
        "SiteRefWGS84_Lon": float(lon),
        "Bron": "BGT pand via PDOK OGC API; RCE rijksmonument 19264",
    })

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    f.write(OUT)
    print("geschreven:", OUT)
    print("schema:", f.schema, "| IfcRoot-entiteiten:", len(f.by_type("IfcRoot")))
    print("site ref RD: X=%.2f Y=%.2f | WGS84 lat=%.7f lon=%.7f" % (x0, y0, lat, lon))
    print("footprint punten (lokaal):", len(exterior), "| opp: %.1f m2" % geom.area)


if __name__ == "__main__":
    sys.exit(main())
