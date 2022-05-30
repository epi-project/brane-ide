# Changelog

All notable changes to the JupyterLab IDE extension for the Brane framework will be documented in this file.


## [0.1.2] - 2022-05-30
### Fixed
- Old command `make brane-ide` being accidentally left in the README.md.

## [0.1.1] - 2022-05-30
### Added
- An extra option to set the `redis` endpoint as required.

### Changed
- The `BRANE_INSTANCE` option to `BRANE_DRV`.

### Fixed
- The IDE having the wrong (default) URL for the `redis` endpoint.

## [0.1.0] - 2022-05-30
### Added
- An official release to the code already there from Onno.

### Changed
- The IDE to not show process anymore, but instead to just simply return the results as they are sent back by brane-drv (or other callbacks).

### Fixed
- The IDE not working with the newest Brane version.
