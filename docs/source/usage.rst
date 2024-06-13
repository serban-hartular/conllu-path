Usage
=====

.. _installation:

Installation
------------

To use conllu-path, first install it using pip:

.. code-block:: console

   (.venv) $ pip install lark
   (.venv) $ pip install -i https://test.pypi.org/simple/ conllu-path-shartular

Loading conllu files
--------------------

To iterate through the sentences in a conllu file,
you can use the ``conllu_path.iter_sentences_from_conllu(filename)`` function:

.. autofunction:: conllu_path.iter_sentences_from_conllu

