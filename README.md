# Grote Kerk Haarlem — IFC4 model

IFC4-model van de **Grote of Sint-Bavokerk**, Grote Markt 22, 2011 RD Haarlem (rijksmonument **nr. 19264**),
gebouwd op basis van 66 bouwtekeningen en gegeorefereerd met open data (BGT / BAG / RCE).

## Georeferentie

| Item | Waarde |
|---|---|
| Primair CRS | **EPSG:28992 — RD New** (Amersfoort / Bessel 1841), hoogte in **NAP** |
| Secundair | WGS84 (EPSG:4326) |
| Site-referentiepunt (BGT-centroid kerk) | RD **X 103936,11 — Y 488399,80** = WGS84 **lat 52,3810896, lon 4,6372217** |
| Rijksmonument-punt 19264 (RCE) | RD X 103972 — Y 488371 = WGS84 lat 52,3808291, lon 4,6377517 |
| BGT-voetafdruk kerkcomplex | ca. 120 × 59 m, **5.249 m²**, RD X 103880,53–104000,36 / Y 488368,75–488428,01 |
| BAG-pand | `0392100000037430` — bouwjaar 1400, bijeenkomstfunctie |

In het IFC4-bestand: `IfcProjectedCRS` (EPSG:28992, geodetisch CRS EPSG:4289) + `IfcSite` via
`IfcMapCoordinate`/`IfcMapCoordinateConversion` (Easting/Northing/OrthogonalHeight in NAP) + `TrueNorth`.

## Bronnen (open data)

- **BGT pand** (voetafdruk): `https://api.pdok.nl/kadaster/bgt/ogc/v1/collections/pand/items`
- **BAG pand**: `https://api.pdok.nl/kadaster/bag/ogc/v2/collections/pand/items`
- **Rijksmonumenten (RCE)** WFS: `https://services.rce.geovoorziening.nl/rce/wfs` (`rce:NationalListedMonumentPoints`)
- **3D BAG** (dakhoogtes, optioneel): `https://api.3dbag.nl/collections/pand`

## Structuur

- `tekeningen/` — de 66 bronafbeeldingen (bladnummers in bestandsnaam)
- `data/` — opgehaalde geodata (JSON) en georeferentie-samenvatting
- `scripts/` — Python-scripts: geodata ophalen, tekeningen analyseren, IFC4 genereren
- `ifc/` — gegenereerde IFC4-bestanden + validatierapport
- `docs/` — Leesmij per fase, bladoverzicht, meetstaat

## Status

- [x] Repo aangemaakt + GitHub App toegang
- [x] Georeferentie opgehaald uit BGT/BAG/RCE
- [x] 42 van 66 tekeningen geanalyseerd (26 geclassificeerd; rest geskipt i.v.m. scan-kwaliteit) — zie `docs/bladen/bladoverzicht.json`
- [x] IFC4 v0 massing (BGT-voetafdruk) + v1 kruisvormige wanden/daken/vieringtoren/deuren + **v2 incl. 3 aangebouwde huisjes** (`ifc/Grote-Kerk-Haarlem_v2.ifc`), EPSG:28992 + NAP
- [x] Validatie GESLAAGD (schema, georeferentie, bbox binnen BGT) — zie `docs/validatie.md`
- [ ] v2: binnenwanden, ramen, trappen, gewelven, NAP-maaiveld uit AHN
