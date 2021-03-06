==========
User Guide
==========
.. _guide:


Knowledge Graphs
================

Basics
------

The knowledge graph class in forayer has two central attributes: `entities` and `rel`. The former contains entities and their attributes. The latter contains relationships between entities. Let's look at a small example.

.. code-block:: python

  >>> from forayer.knowledge_graph import KG
  >>> entities = {"e1": {"a1": "first entity", "a2": 123}, "e2": {"a1": "second ent"}, "e3": {"a2": 124}}
  >>> relations = {"e1": {"e3": "somerelation"}}
  >>> kg = KG(entities=entities, rel=relations, name="mykg")
  >>> kg
  KG(entities={'e1': {'a1': 'first entity', 'a2': 123}, 'e2': {'a1': 'second ent'}, 'e3': {'a2': 124}},
  rel={'e1': {'e3': 'somerelation'}}, name=mykg)


Entities are dictionaries with entity ids as keys and attribute dictionaries. Relations have a similar structure, with entity ids of the edge source as keys and a dictionary with the entity id of the edge target as key and the relation name as attribute value. Forayer also allows you to have more complicated relation attributes than just the name:

.. code-block:: python

  >>> kg.add_rel("e1","e3", {"relation_name": {"rel_att":1}})
  >>> kg
  KG(entities={'e1': {'a1': 'first entity', 'a2': 123}, 'e2': {'a1': 'second ent'}, 'e3': {'a2': 124}},
  rel={'e1': {'e3': ['somerelation', {'relation_name': {'rel_att': 1}}]}}, name=mykg)

You can also easily get more general informations about the graph:

.. code-block:: python

  >>> kg.info()
  'mykg: (# entities: 3, # entities_with_rel: 2, # rel: 2, # entities_with_attributes: 3, # attributes: 3, # attr_values: 4)'
  # ids of all entities
  >>> kg.entity_ids
  {'e2', 'e1', 'e3'}

  # name of all attributes
  >>> kg.attribute_names
  {'a1', 'a2'}

  # name of all relations
  >>> kg.relation_names
  {'somerelation', 'relation_name'}

Exploring the knowledge graph
-----------------------------

You can access the attributes of an entity via the bracket operator:

.. code-block:: python

  >>> kg["e1"]
  {'a1': 'first entity', 'a2': 123}

If you provide a list of entities you can get information about multiple entities:

.. code-block:: python

  >>> kg[["e1","e2"]]
  {'e1': {'a1': 'first entity', 'a2': 123}, 'e2': {'a1': 'second ent'}}

You can access the relations of an entity:

.. code-block:: python

  >>> kg.rel["e1"]
  {'e3': ['somerelation', {'relation_name': {'rel_att': 1}}]}

You can search for entities with certain attribute values:

.. code-block:: python

  >>> kg.search("first")
  {'e1': {'a1': 'first entity', 'a2': 123}}

Search for entities with specific attributes:

.. code-block:: python

  >>> kg.with_attr("a1")
  {'e1': {'a1': 'first entity', 'a2': 123}, 'e2': {'a1': 'second ent'}}

With the knowledge graphs you can perform basic exploratory actions like looking at neighbors of entities:

.. code-block:: python

  >>> kg.neighbors("e1")
  {'e3': {'a2': 124}}

Getting a sample graph with a certain number of entities:

.. code-block:: python

  >>> kg.sample(2)
  KG(entities={'e2': {'a1': 'second ent'}, 'e3': {'a2': 124}}, rel={'e1': {'e3': ['somerelation', {'relation_name': {'rel_att': 1}}]}, name=mykg)

Get a subgraph with specific entities:

.. code-block:: python

  >>> kg.subgraph(["e1","e3"])
  KG(entities={'e1': {'a1': 'first entity', 'a2': 123}, 'e3': {'a2': 124}},
  rel={'e1': {'e3': ['somerelation', {'relation_name': {'rel_att': 1}}]}}, name=mykg)

Manipulating the graph
----------------------

You can also add and remove entities as well as relations:

.. code-block:: python

  >>> kg.add_entity("e4", {"a1":"new"})
  >>> kg.remove_entity("e3")
  >>> kg.add_rel("e1","e4","newrel")
  >>> kg
  KG(entities={'e1': {'a1': 'first entity', 'a2': 123}, 'e2': {'a1': 'second ent'}, 'e4': {'a1': 'new'}},
  rel={'e1': {'e4': 'newrel'}}, name=mykg)
  >>> kg.remove_rel("e1","e4")
  >>> kg
  KG(entities={'e1': {'a1': 'first entity', 'a2': 123}, 'e2': {'a1': 'second ent'}, 'e4': {'a1': 'new'}},
  rel={}, name=mykg)

Entity Resolution
=================

Load benchmarks
---------------

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
  # attributes: 14, # attr_values: 115)
  },
  ClusterHelper(# elements:20, # clusters:10))

For all sampling methods in forayer it is possible to provide a seed for reproducibility.

.. code-block:: python

    >>> c_sample = ds.er_task.clusters.sample(20,seed=10)

ClusterHelper
-------------

The `ClusterHelper` contains the known matches. You can find the cluster to which an entity belongs, and what entities belong to what cluster:

.. code-block:: python

  >>> clusters = ds.er_task.clusters
  >>> clusters.elements('http://www.wikidata.org/entity/Q2060044')
  11984
  # get members of cluster either via bracket operator
  >>> clusters[11984]
  {'http://www.wikidata.org/entity/Q2060044', 'http://dbpedia.org/resource/E083028'}
  # or with the members method 
  >>> clusters.members(11984)
  {'http://www.wikidata.org/entity/Q2060044', 'http://dbpedia.org/resource/E083028'}

To make things easier you can also directly find linked entities.

.. code-block:: python

  >>> clusters.links('http://www.wikidata.org/entity/Q2060044')
  'http://dbpedia.org/resource/E083028'

To look at some more convenient functions, lets create an example ClusterHelper object with some bigger clusters:

.. code-block:: python

    >>> from foryer.knowledge_graph import ClusterHelper
    >>> ch = ClusterHelper([{"a1", "1", "b1"}, {"a2", "2"}, {"a3", "3"}])

You can get inner-cluster links as pairs with :meth:`~forayer.knowledge_graph.ClusterHelper.all_pairs` (the function returns a generator):

.. code-block:: python

    >>> list(ch.all_pairs("a1"))
    [('1', 'b1'), ('1', 'a1'), ('b1', 'a1')]

When you don't want the links of a specific entity you can also get all links if you do not provide an argument:

.. code-block:: python

    >>> list(ch.all_pairs())
    [('1', 'b1'), ('1', 'a1'), ('b1', 'a1'), ('2', 'a2'), ('3', 'a3')]

The `__contains__` function is smartly overloaded to let you do a lot of nice things:

.. code-block:: python

    # check if an entity is contained
    >>> "a1" in ch
    True
    # check if a cluster id is assigned
    >>> 0 in ch
    True
    # check if a cluster is contained
    >>> {"a2","2"} in ch
    True
    # use tuples to check if a link is contained
    >>> ("1","b1") in ch
    True

You can add and remove clusters and links:

.. code-block:: python

    # Notice that adding a link into an existing cluster
    # links this entity to all other clusters as well
    # through transitivity
    >>> ch.add_link("a1","c1")
    >>> print(ch)
    {0: {'1', 'a1', 'b1', 'c1'}, 1: {'2', 'a2'}, 2: {'a3', '3'}}
    >>> ch.remove("c1")
    >>> print(ch)
    {0: {'1', 'a1', 'b1'}, 1: {'2', 'a2'}, 2: {'a3', '3'}}
    # You can also add via cluster id
    >>> ch.add_to_cluster(0,"c1")
    >>> print(ch)
    {0: {'1', 'a1', 'b1', 'c1'}, 1: {'2', 'a2'}, 2: {'a3', '3'}}
    # You can remove entire clusters
    >>> ch.remove_cluster(1)
    >>> print(ch)
    {0: {'1', 'a1', 'b1', 'c1'}, 2: {'a3', '3'}}
    # Adding entire clusters is possible as well
    >>> ch.add({"e1","f1"})
    >>> print(ch)
    {0: {'1', 'a1', 'b1', 'c1'}, 2: {'a3', '3'}, 3: {'f1', 'e1'}}


Loading and writing data
========================
Forayer enables you to load data from different dataformats.

RDF Data
--------
Loading knowledge graphs from rdf datasources is very simple and all common serialization formats are supported. Even remote files can be loaded:

.. code-block:: python

    >>> from forayer.input_output.from_to_rdf import load_from_rdf
    >>> kg = load_from_rdf("http://www.w3.org/People/Berners-Lee/card")
    >>> kg['https://www.w3.org/People/Berners-Lee/card#i']['http://xmlns.com/foaf/0.1/givenname']
    'Timothy'

Writing is similarly easy:

.. code-block:: python

    >>> from forayer.input_output.from_to_rdf import write_to_rdf
    >>> out_path = ...
    >>> write_to_rdf(kg, out_path=out_path, format="turtle")

Gradoop CSV Datasource
----------------------
You can load and write data from the `Gradoop format <https://github.com/dbs-leipzig/gradoop/wiki/Gradoop-DataSources#CSVDataSource>`_:

.. code-block:: python

    >>> from forayer.input_output.from_to_gradoop import load_from_csv_datasource

    >>> data_folder_path = ...
    >>> kgs = load_from_csv_datasource(data_folder_path)

Since Gradoop gives graphs a specific type label you can either have that as a graph name, or specify a different property for the graph_name with the `graph_name_property` keyword.
The loaded `kgs` is a dictionary of graph names and graphs.

For writing you have to provide all vertices with a special attribute "_label" or provide another attribute that could be used instead to specify the graph type.

.. code-block:: python

    >>> from forayer.input_output.from_to_gradoop import write_to_csv_datasource

    >>> out_path = ...
    >>> write_to_csv_datasource(kgs, out_path)

For more information on in- and outputs see the :ref:`API reference <io_ref>` for the input_output module.

Create your own ERTask
======================
If you have your own knowledge graphs and gold standard cluster/links you can create your own ERTask. Let's look at a small toy example:

.. code-block:: python

    >>> from forayer.knowledge_graph import KG, ERTask, ClusterHelper
    >>> entities_1 = {
            "kg_1_e1": {"a1": "first entity", "a2": 123},
            "kg_1_e2": {"a1": "second ent"},
            "kg_1_e3": {"a2": 124},
        }
    >>> rel_1 = {"kg_1_e1": {"kg_1_e3": "somerelation"}}
    >>> kg1 = KG(entities_1, rel_1, name="kg1")
    >>> entities_2 = {
            "kg_2_e1": {"a5": "first entity", "a2": 123},
            "kg_2_e2": {"a6": "other second ent"},
            "kg_2_e3": {"a7": 123},
        }
    >>> rel_2 = {"kg_2_e1": {"kg_2_e3": "someotherrelation"}}
    >>> kg2 = KG(entities_2, rel_2, name="kg2")
    >>> clusters = ClusterHelper([{"kg_1_e1", "kg_2_e1"}, {"kg_1_e2", "kg_2_e2"}, {"kg_1_e3", "kg_2_e3"}])
    >>> ert = ERTask([kg1, kg2],clusters)
    >>> ert
    ERTask({kg1: (# entities: 3, # entities_with_rel: 2, # rel: 1, # entities_with_attributes: 3, # attributes: 3, # attr_values: 4),
    kg2: (# entities: 3, # entities_with_rel: 2, # rel: 1, # entities_with_attributes: 3, # attributes: 3, # attr_values: 3)},
    ClusterHelper(# elements:6, # clusters:3))


Interactive Exploration
=======================
To get a better understanding of the data you are working with certain common plotting possibilities are already provided. For an overview look int `the notebooks folder <https://github.com/dobraczka/forayer/tree/main/notebooks>`_.
