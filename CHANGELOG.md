# Changelog

All notable changes to BioQuiet Backend will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [1.0.0] - 2026-03-18

### Added
- REST API endpoint `GET /api/v1/zepa` to query ZEPA protected zones by bounding box (WGS84 decimal degrees)
- Spatial intersection queries returning zone name, geometry, and noise thresholds
- Noise threshold reference values: 45 dB (safe) and 60 dB (warning) based on natural spaces regulation and scientific literature
- Ecological metadata per zone:
  - Habitats (Annex I of the Habitats Directive)
  - Species: birds, mammals, plants, and invertebrates (Annexes I/II)
  - Impacts and threats (code, description, intensity, occurrence)
  - Management body (organization, contact, conservation measures)
- Dataset of 602 ZEPA zones from Red Natura 2000 cartography (MITECO, December 2024), licensed CC BY 4.0
- Metadata from CNTRYES database (MITECO, end of 2023), licensed CC BY 4.0
- OpenAPI 3.1.0 specification
- CI/CD workflow for automatic OpenAPI docs deployment to GitHub Pages
