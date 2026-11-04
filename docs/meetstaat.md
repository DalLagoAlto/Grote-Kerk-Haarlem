# Meetstaat — maten uit de 42 restauratietekeningen (Grote of St. Bavokerk, Haarlem)

Bron: 42 foto's `20251111_*.jpg` (repo-root), geclassificeerd in `docs/bladen/bladoverzicht.json`.
De overige 24 bladen zijn overgeslagen (scan-kwaliteit onvoldoende,指示 user).

## Plattegrond blad 1 (bestand 20251111_111204.jpg, schaal 1:100) — hoofdafmetingen
- Totale lengte (W-O): **118,00 m** · totale breedte (N-Z): 74,00 m volgens tekening (BGT-geregistreerd: 119,8 × 59,3 m)
- Schip: **74,00 × 24,00 m** · Koor: **44,00 × 24,00 m** · Transept: 44,00 m N-Z
- Wanddikte buitenmuren: **1,00 m**
- Vieringtoren centraal op kruising schip/transept
- Deuren: west hoofdingang **4,00 m**, transept N/Z **3,00 m**, koor O **3,00 m**
- Rasterassen A–F (W-O) en 1–9 (Z-N); noord = boven

## Hoogtes (gevels + doorsnedes)
- Zijbeuk/lage delen: goot **+10 m**, nok **+15 m** (20251111_110940.jpg)
- Hoofdwerk westgevel: **+21 m** (goot) en **+29 m** (nok) (20251111_110053.jpg, 110032.jpg blad B81)
- Doorsnede: 11,84 m totaal / 7,47 m tot muurpunt (20251111_112138.jpg); 5,34–20,65 m (20251111_110750.jpg)
- Vieringtoren: **78 m** (openbare bron; indicatief in model), torenbreedte **7,37 m** (B81: 737 cm)
- Detail B/31 Kap Brouwerskapel (1:50): kap **5,84 m breed × 3,71 m hoog**, wand **0,24 m** (20251111_112107.jpg)
- Ramen indicatief: **2,40 m breed × 1,50 m hoog** (20251111_112138.jpg)

## Gebruikt in IFC4 v1 (`ifc/Grote-Kerk-Haarlem_v1.ifc`)
- Kruisvorm: schip 74×24, koor 44×24, transept 36 m breed over BGT-breedte; wanddikte 1,00 m
- Wanden tot goot **+21 m**; zadeldaken schip+koor en transept met nok **+29 m**
- Vieringtoren 7,37×7,37 m op de kruising, schacht tot +21 m, spits (indicatief) tot **+78 m**
- 4 deuren (4,00 / 3,00 / 3,00 / 3,00 m, hoogte 3,00 m)
- Terreinplaat = BGT-voetafdruk (exact)
- Georeferentie: EPSG:28992 + NAP; site-ref = BGT-centroid RD X 103936,21 / Y 488400,36 = WGS84 52,3810896 / 4,6372217

## Aannames / niet gemodelleerd in v1
- Binnenwanden, zijbeukscheidingen, galerijen, trappen, gewelven: niet leesbaar uit de foto's → v2
- Raamopeningen in wanden (alleen maten indicatief) → v2
- Toren spits als vierkante proxy (geen taper) → v2
- NAP-maaiveld van het terrein nog niet uit AHN; RefElevation = 0,00
- BGT-breedte (59,3 m) is smaller dan de 74 m op de plattegrond; model folgt BGT voor de buitenomtrek
