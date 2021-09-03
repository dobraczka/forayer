.. _entity_resolution:

====================
ERTasks and Datasets
====================

Forayer comes with some datasets, that can be easily loaded (for an overview see :ref:`here<datasets_ref>`)

.. code-block:: python

  >>> from forayer.datasets import OpenEADataset
  >>> ds = OpenEADataset(ds_pair="D_W",size="15K",version=1)

Datasets that are entity resolution tasks contain an `ERTask` attribute, which has the knowledge graphs that should be matched and the known matches.

.. code-block:: python

  >>> ds.er_task
  ERTask({
    DBpedia: (# entities: 15000, # entities_with_rel: 15000,
    # rel: 13359, # entities_with_attributes: 13782,
    # attributes: 13782, # attr_values: 24995),
    Wikidata: (# entities: 15000, # entities_with_rel: 15000,
    # rel: 13554, # entities_with_attributes: 14376,
    # attributes: 14376, # attr_values: 114107)
    },
    ClusterHelper(# elements:30000, # clusters:15000))

You can access the knowledge graphs by their names:

.. code-block:: python

  >>> dbpedia = ds.er_task.kgs["DBpedia"]

The `ClusterHelper` contains the known matches. You can find to which cluster an entity belongs, and what entities belong to what cluster:

.. code-block:: python

  >>> clusters = ds.er_task.clusters
  >>> clusters['http://www.wikidata.org/entity/Q2060044']
  11984
  >>> clusters[11984]
  {'http://www.wikidata.org/entity/Q2060044', 'http://dbpedia.org/resource/E083028'}

To make things easier you can also directly find linked entities.

.. code-block:: python

  >>> clusters.links('http://www.wikidata.org/entity/Q2060044')
  'http://dbpedia.org/resource/E083028'

For prototyping it is usually beneficial to work with part of a dataset. You can therefore sample the ERTask.

.. code-block:: python

  >>> ds.er_task.sample(10)
  ERTask({
    DBpedia: (# entities: 10, # entities_with_rel: 2,
    # rel: 2, # entities_with_attributes: 10,
    # attributes: 10, # attr_values: 35),
    Wikidata: (# entities: 10, # entities_with_rel: 2,
    # rel: 2, # entities_with_attributes: 10,
    # attributes: 10, # attr_values: 100)},
    ClusterHelper(# elements:20, # clusters:10))

This takes 10 matched entities. If you want non-matches in your sample as well this is also possible:

.. code-block:: python

  >>> ds.er_task.sample(10,unmatched=10)
  ERTask({
  DBpedia: (# entities: 16, # entities_with_rel: 0,
  # rel: 0, # entities_with_attributes: 16,
  # attributes: 16, # attr_values: 59),
  Wikidata: (# entities: 14, # entities_with_rel: 0,
  # rel: 0, # entities_with_attributes: 14,
  # attributes: 14, # attr_values: 115)},
  ClusterHelper(# elements:20, # clusters:10))

For all sampling methods in forayer it is possible to provide a seed for reproducibility.
