# Validatierapport — Grote-Kerk-Haarlem_v2.ifc

- IFC-schema: `IFC4`
- Entiteiten totaal: 598
  - IfcProject: 1
  - IfcSite: 1
  - IfcBuilding: 1
  - IfcBuildingStorey: 1
  - IfcWall: 16
  - IfcSlab: 1
  - IfcRoof: 5
  - IfcBuildingElementProxy: 4
  - IfcProjectedCRS: 1
  - IfcMapConversion: 1
  - IfcPropertySet: 7
- IfcMapConversion: TargetCRS=`EPSG:28992`, Eastings=103936.21, Northings=488400.36, OrthogonalHeight=0.00, rot=(1.000,0.000), scale=1.000
- IfcSite: RefLatitude=52.3810896 RefLongitude=4.6372217 RefElevation=0.00 (verwacht WGS84 52.3810896 / 4.6372217)
- Geometrie: 30 elementen, 2340 vertices, OK
- BBox model in RD: X 103880.53..104000.36 Y 488368.43..488428.01
- BBox BGT : X 103880.53..104000.36 Y 488368.43..488428.01

## Resultaat
- schema IFC4: OK
- georeferentie (EPSG:28992 + map conversion op site-ref): OK
- IfcSite RefLat/Lon = WGS84 site-ref: OK
- geometrie leesbaar: OK
- bbox model binnen BGT-voetafdruk (+0.5 m): OK
- **TOTAAL: GESLAAGD**
