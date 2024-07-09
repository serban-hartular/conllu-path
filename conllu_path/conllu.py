from __future__ import annotations

import typing
import warnings
from io import StringIO
from typing import Dict, List, Generator
from conllu_path.exception import ConlluException
from conllu_path.tree import Tree
from conllu_path.node_id import NodeID
from conllu_path.node_data import FixedKeysNode, DictNode
from conllu_path.sentence import Sentence

conllu_fields = ('id', 'form', 'lemma', 'upos', 'xpos', 'feats',
                 'head', 'deprel', 'deps', 'misc')
conllu_index_dict = {k:i for i, k in enumerate(conllu_fields)}
field_is_dict = ('feats', 'misc')
field_is_set = ('deps',)
EMPTY_FIELD = '_'
DICT_SET_ITEM_SPLIT = '|'
KEY_VAL_SEP = {'feats': '=', 'misc' : '=', }
MANY_VALS_SEP = ','


def conllu_to_node(source : str, line_nr : int = None) -> Tree:
    data_fields = source.strip().split('\t')
    # if len(data_fields) != len(conllu_fields):
    #     raise ConlluException(source, 'Invalid nr of fields', line_nr)
    data_list = []
    for label, data_str in zip(conllu_fields, data_fields):
        # if not data_str or data_str == EMPTY_FIELD:
        #     data_list.append(None)
        if not data_str or data_str == EMPTY_FIELD:
            data_str = None

        if label in field_is_dict:
            #this field contains a dict
            items = [] if data_str is None else data_str.split(DICT_SET_ITEM_SPLIT)
            item_dict = {}
            for kv_pair in items: # not pythonic, but allows dealing with erroneous data
                if kv_pair.count(KEY_VAL_SEP[label]) != 1:
                    warnings.warn('Error in field %s, line %d: no key-value separator (%s) present' % (label, line_nr, KEY_VAL_SEP[label]))
                if KEY_VAL_SEP[label] not in kv_pair:
                    k,v = kv_pair, ['NONE']
                else:
                    k,v = kv_pair.split(KEY_VAL_SEP[label], 1)
                    v = v.split(MANY_VALS_SEP)
                item_dict[k] = v
            # item_dict = {t[0]:set(t[1].split(MANY_VALS_SEP))
            #              for t in (s.split(KEY_VAL_SEP[label], 1) for s in items)}
            data_list.append(DictNode(item_dict))
        elif label in field_is_set:
            items = () if data_str is None else data_str.split(DICT_SET_ITEM_SPLIT)
            # data_list.append(set(items))
            data_list.append(items)
        else:
            data_list.append('' if data_str is None else data_str)
    data = FixedKeysNode(data_list, conllu_index_dict)
    return Tree(data.sdata('id'), data)

def node_to_conllu(node : Tree) -> str:
    node = node.to_dict()
    data_list = []
    for label in conllu_fields:
        data = node.get(label)
        if not data:
            data = EMPTY_FIELD
        elif isinstance(data, str):
            pass
            # data = data if data else EMPTY_FIELD
        elif isinstance(data, Dict):
            data =\
                DICT_SET_ITEM_SPLIT.join(
                    KEY_VAL_SEP[label].join([
                        k, MANY_VALS_SEP.join(v) if not isinstance(v, str) else v
                ])
            for k,v in data.items())
        elif isinstance(data, typing.Iterable):
            data = MANY_VALS_SEP.join([str(i) for i in data])
        elif isinstance(data, int) or isinstance(data, float):
            data = str(data)
        else:
            raise ConlluException(str(data),
                    'Cannot transform %s item to conllu in %s' % (label, str(node)))
        data_list.append(data)
    return '\t'.join(data_list)

def sentence_to_conllu(sentence : Sentence) -> str:
    output = ''.join(['# %s\n' % m for m in sentence.meta]) if sentence.meta else ''
    output += '# sent_id = %s\n' % str(sentence.sent_id)
    output += '# text = %s\n' % str(sentence.text)
    for node in sentence.sequence:
        output += node_to_conllu(node) + '\n'
    output += '\n'
    return output

def iter_sentences_from_conllu(file : typing.TextIO | str) -> Generator[Sentence, None, None]:
    """
    Returns an iterator of sentences from the conllu file

    :param file: filename or string buffer.
    :type kind: str or TextIO
    :return: Generator of sentences.
    :rtype: Generator[Sentence, None, None]
    """
    if isinstance(file, str):
        file = open(file, 'r', encoding='utf-8')
    line_nr = 0
    node_sequence = []
    meta_data = []
    special_data = {} # text, sent_id
    while True:
        line = file.readline()
        line_nr += 1
        if not line:
            break
        line = line.strip()
        if not line:
            # blank line - yield sentence if have sentence
            if node_sequence:
                if meta_data: # add metadata to sentence **kwargs
                    special_data.update({'meta':meta_data})
                sentence = Sentence(node_sequence, **(special_data))
                if not sentence.root:
                    warnings.warn('Error building sentence sent_id = %s: %s' % (sentence.sent_id, sentence.sanity_comment))
                node_sequence = []
                meta_data = []
                special_data = {}  # text, sent_id
                yield sentence
            continue
        if line[0] == '#':# comment
            line = line[1:] # strip #
            if '=' in line: # check for sent_id, text
                k,arg = line.split('=',1)
                k, arg = k.strip(), arg.strip()
                if k in ('sent_id', 'text'):
                    special_data[k] = arg
                    continue
            meta_data.append(line.strip())
            continue
        node_sequence.append(conllu_to_node(line, line_nr))
    if node_sequence:
        if meta_data:  # add metadata to sentence **kwargs
            special_data.update({'meta': meta_data})
        yield Sentence(node_sequence, **(special_data))
    file.close()

def iter_sentences_from_conllu_str(conllu_str: str) -> Generator[Sentence, None, None]:
    return iter_sentences_from_conllu(StringIO(conllu_str))

