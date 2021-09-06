<p align="center">
<img src="https://github.com/dobraczka/forayer/raw/main/docs/forayerlogo.png" alt="forayer logo", width=200/>
</p>

<h2 align="center"> forayer</h2>

<p align="center">
<a href="https://github.com/dobraczka/forayer/actions/workflows/main.yml"><img alt="Tests" src="https://github.com/dobraczka/forayer/actions/workflows/tests.yml/badge.svg?branch=main"></a>
<a href="https://github.com/dobraczka/forayer/actions/workflows/quality.yml"><img alt="Linting" src="https://github.com/dobraczka/forayer/actions/workflows/quality.yml/badge.svg?branch=main"></a>
<a><img alt="Test coverage" src="https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/dobraczka/6d07d95e43929bcbf9d031c2c8f2015f/raw/forayer_test_gist.json"></a>
<a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
</p>

About
=====
Forayer is a library of **f**irst aid utilities for kn**o**wledge g**r**aph explor**a**tion with an entit**y** c**e**ntric app**r**oach.
It is intended to make data integration of knowledge graphs easier. With entities as first class citizens forayer is a toolset to aid in knowledge graph exploration for data integration and specifically entity resolution.

You can easily load pre-existing entity resolution tasks:

```python
  >>> from forayer.datasets import OpenEADataset
  >>> ds = OpenEADataset(ds_pair="D_W",size="15K",version=1)
  >>> ds.er_task
  ERTask({DBpedia: (# entities: 15000, # entities_with_rel: 15000, # rel: 13359,
  # entities_with_attributes: 13782, # attributes: 13782, # attr_values: 24995),
  Wikidata: (# entities: 15000, # entities_with_rel: 15000, # rel: 13554,
  # entities_with_attributes: 14376, # attributes: 14376, # attr_values: 114107)},
  ClusterHelper(# elements:30000, # clusters:15000))
```

This entity resolution task holds 2 knowledge graphs and a cluster of known matches. You can search in knowledge graphs:

```python
  >>> ds.er_task["DBpedia"].search("Dorothea")
  KG(entities={'http://dbpedia.org/resource/E801200': 
  {'http://dbpedia.org/ontology/activeYearsStartYear': '"1948"^^<http://www.w3.org/2001/XMLSchema#gYear>',
  'http://dbpedia.org/ontology/activeYearsEndYear': '"2008"^^<http://www.w3.org/2001/XMLSchema#gYear>',
  'http://dbpedia.org/ontology/birthName': 'Dorothea Carothers Allen',
  'http://dbpedia.org/ontology/alias': 'Allen, Dorothea Carothers',
  'http://dbpedia.org/ontology/birthYear': '"1923"^^<http://www.w3.org/2001/XMLSchema#gYear>',
  'http://purl.org/dc/elements/1.1/description': 'Film editor',
  'http://dbpedia.org/ontology/birthDate': '"1923-12-03"^^<http://www.w3.org/2001/XMLSchema#date>',
  'http://dbpedia.org/ontology/deathDate': '"2010-04-17"^^<http://www.w3.org/2001/XMLSchema#date>', 
  'http://dbpedia.org/ontology/deathYear': '"2010"^^<http://www.w3.org/2001/XMLSchema#gYear>'}}, rel={}, name=DBpedia)
```

Decide to work with a smaller snippet of the resolution task:

```python
  >>> ert_sample = ds.er_task.sample(100)
  >>> ert_sample
  ERTask({DBpedia: (# entities: 100, # entities_with_rel: 6, # rel: 4,
  # entities_with_attributes: 99, # attributes: 99, # attr_values: 274),
  Wikidata: (# entities: 100, # entities_with_rel: 4, # rel: 4,
  # entities_with_attributes: 100, # attributes: 100, # attr_values: 797)},
  ClusterHelper(# elements:200, # clusters:100))
```

And much more can be found in the [user guide](https://forayer.readthedocs.io/en/latest/source/user_guide.html).

Installation
============

You can install forayer via pip:

```bash
  pip install forayer
```
