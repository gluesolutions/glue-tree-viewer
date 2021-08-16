****************************************
Tree Viewer User Tutorial
****************************************

    :keywords: Tutorial, Documentation

Contact with any questions: Tommy Morriss, thmorriss@gmail.com

Introduction
============

This document explains how to use tree data types, and the tree viewer in the glue environment.

Importing Tree Objects
=======================

There are two ways to import tree objects.

..
  this section determined by config.py

#. Open a dendrogram .fits file exported by astrodendro, selecting ``Tree Dendogram``
   This will load the dendrogram image (2d or 3d) AND the tree, and they will be automatically linked together.

#. Open any newick formatted file (typically .nw or .tre but can be anything), and selecting ``Newick Tree Loader``
   This will load only the the tree file, and it will be unlinked.

Newick Tree Format
=======================

The newick format is the main format for importing trees. Other formats may be trivially added, contact author for requests.
The format is described `here`_. The values that the plugin uses to link are the "names" described in the link.
By default format=1 is chosen as the newick type.
It will try to detect "support values" and ignore them, that logic is in the method ``determine_format`` of config.py if you are interested.

.. _here: http://etetoolkit.org/docs/latest/tutorial/tutorial_trees.html#reading-and-writing-newick-trees 

Linking Semantics
=================

Traditional `linking in glue`_ does not work with trees.
Traditional linking ties together attributes that have the same unit of measurement.
The values stored in the trees don't have any units, and thus cant be glued to any other dataset.
Rather, each value in a tree is a keyvalue describing a specific entity.
These entities might exist in other datasets, thus some sort of link (and the brushing/linking that follows) would be useful.
Tree keyvalues are linked in way very similar to sql table joins. The full semantics are described `here`_.
A (rough) visual guide is in this `presentation`_.

.. _linking in glue: http://docs.glueviz.org/en/stable/gui_guide/link_tutorial.html
.. _here: http://docs.glueviz.org/en/stable/api/glue.core.data.Data.html#glue.core.data.Data.join_on_key
.. _presentation: https://docs.google.com/presentation/d/1Jr_soBpESsS3TnKi1oQtUn2qNYyclVWNkJ0dwWyny6U/edit?usp=sharing


Linking From the UI
===================
For advanced users and links, importing a tree, then linking it can be done from the ipython terminal using the ``join_on_key`` method.
For simple links, select the two attributes that represent entity keyvalues, and click ``Create advanced link -> Tree Viewer -> Join On Key``
NOTE: As of now, there is now way to unjoin datasets.

Viewer Navigation
===================
TODO

Viewer Selection
===================
TODO
