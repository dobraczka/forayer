# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

## [0.4.4] - 2023-03-28

### Fixed

- Loosen python dependency restriction

## [0.4.3] - 2022-10-19

### Fixed

- Fixed joblib vulnerability

## [0.4.2] - 2022-06-10

### Fixed

- Fixed bug in knowledge graph representation


## [0.4.1] - 2022-02-17

### Fixed

- Fixed security vulnerability in IPython by setting it to at least 7.31.1

## [0.4.0] - 2022-01-17

### Fixed

- Fixed bug with multi-value triples

### Changed

- Moved data storage to pystow

## [0.3.3] - 2021-11-24

### Fixed

- Update and cleanup dependencies
- Fix bug with int relations and .info() function


## [0.3.2] - 2021-10-14

### Fixed

- Fix unnecessary download of word embeddings

## [0.3.1] - 2021-10-14

### Fixed

- Fix problem with error message in AttributeVectorizer with empty path

## [0.3.0] - 2021-09-20

### Added

- Generalized ClusterHelper to allow more types for entity (and cluster) ids
- Added more method for manipulation of ClusterHelper


## [0.2.0] - 2021-09-10

### Added

- Merge overlapping clusters when initializing ClusterHelper
- Added some convenience functions in ClusterHelper: all_pairs, number_of_links, enhanced contains function
- Added entity resolution quality metrics

## [0.1.0] - 2021-09-06

- First release

[0.4.4]: https://github.com/dobraczka/forayer/releases/tag/0.4.4
[0.4.3]: https://github.com/dobraczka/forayer/releases/tag/0.4.3
[0.4.2]: https://github.com/dobraczka/forayer/releases/tag/0.4.2
[0.4.1]: https://github.com/dobraczka/forayer/releases/tag/0.4.1
[0.4.0]: https://github.com/dobraczka/forayer/releases/tag/0.4.0
[0.3.3]: https://github.com/dobraczka/forayer/releases/tag/0.3.3
[0.3.2]: https://github.com/dobraczka/forayer/releases/tag/0.3.2
[0.3.1]: https://github.com/dobraczka/forayer/releases/tag/0.3.1
[0.3.0]: https://github.com/dobraczka/forayer/releases/tag/0.3.0
[0.2.0]: https://github.com/dobraczka/forayer/releases/tag/0.2.0
[0.1.0]: https://github.com/dobraczka/forayer/releases/tag/0.1.0
