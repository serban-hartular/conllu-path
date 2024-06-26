.. conllu-path documentation master file, created by
   sphinx-quickstart on Thu Jun 13 10:09:02 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to ``conllu-path``'s documentation!
===========================================

.. note::

   This project is under active development.

``conllu-path`` is a python library for searching conllu trees. It was inspired by
the ``xpath`` XML query language, hence the name. It grew out of the need
(related to a PhD thesis) to search for various syntactic patterns in syntactically
annotated corpora. These were either `Universal Dependencies
<https://universaldependencies.org/>`_
corpora or files generated by parsers trained on the above.
So this library targets ``conllu`` format files.

Searching for syntactic patterns programmatically using existing conllu libraries
-- for instance, detecting
if a node is a verb and has a child that is a noun and that child has a child
that is a preposition whose lemma is *on*:

>>> for node in sentence:
...   if node.upos=='VERB':
...     for child1 in node.children:
...       if child1.upos=='NOUN':
...         for child2 in child1.children:
...           if child2.upos=='ADP' and child2.lemma=='on':
...             report_something(node)

gets old very quickly. ``conllu-path`` replaces this kind of code with a search
that looks like this:

>>> for node in sentence.search('.//[upos=VERB]/[upos=NOUN]/[upos=ADP lemma=on]'):
...   report_something(node)

The API and the description/specs of the search expression language are in
the works. For now, check out the :doc:`usage` section for a quick tutorial.

Contents
--------

.. toctree::

    usage

