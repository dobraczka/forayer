.. _knowledge_graphs:

================
Knowledge Graphs
================

Basics
------

The knowledge graph class in forayer has two central attributes: `entities` and `rel`. The former contains entities and their attributes. The latter contains relationships between entities. Let's look at a small example.

.. code-block:: python

  >>> from forayer.knowledge_graph import KG
  >>> entities = { "e1": {"a1": "first entity", "a2": 123}, "e2": {"a1": "second ent"}, "e3": {"a2": 124}, }
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
