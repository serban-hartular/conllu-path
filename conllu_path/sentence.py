from __future__ import annotations

import warnings
from collections import defaultdict, Counter
from typing import List, Generator, Dict

import conllu_path
from conllu_path.node_id import NodeID
from conllu_path.tree import Tree
from conllu_path.search import Search, Match

class Sentence:
    """Sentence class consists of a tree structure, built from a sequence of nodes.

    The __init__ method may be documented in either the class level
    docstring, or as a docstring on the __init__ method itself.

    Either form is acceptable, but the two should not be mixed. Choose one
    convention to document the __init__ method and be consistent with it.

    Note:
        Do not include the `self` parameter in the ``Args`` section.

    Args:
        msg (str): Human readable string describing the exception.
        code (:obj:`int`, optional): Error code.

    Attributes:
        sequence (List[Tree]): Human readable string describing the exception.
        sent_id (str): Exception error code.

    """
    def __init__(self, node_sequence : List[Tree], **kwargs):
        self.sequence = node_sequence
        self.sent_id = kwargs.get('sent_id')
        self.text = kwargs.get('text')
        self.meta = kwargs.get('meta')
        self._id_dict = {n.id():n for n in self.sequence}
        self.root = None
        self.sanity_comment = ''
        self._is_good = self.sanity_check()
        if self._is_good:
            self.build_tree()

    def iter_nodes(self, from_node : Tree = None, **kwargs) -> Generator[Tree, None, None]:
        try:
            start_index = self.sequence.index(from_node) if from_node else 0
        except:
            raise Exception('Could not find node %s in sentence %s' % (str(from_node), str(self)))
        multiwords = kwargs.get('multiwords')
        multiwords_options = ('words', 'tokens', 'both')
        if multiwords is None:
            multiwords = 'tokens'
        elif multiwords not in multiwords_options:
            raise Exception('Bad value multiword="%s", should be one of %s' % (str(multiwords), str(multiwords_options)))
        elided = bool(kwargs.get('elided'))
        latest_multiword = None
        for n in self.sequence[start_index:]:
            if n.id().elided() and not elided:
                continue # skip elided
            if n.id().multiword():
                latest_multiword = n
                if multiwords == 'tokens':
                    continue # skip multiword
            if latest_multiword and n.id() in latest_multiword.id() and multiwords == 'multiwords':
                continue # displaying multiwords but not tokens they consist of
            yield n

    def sanity_check(self) -> bool:
        ids = [n.id() for n in self.sequence]
        if not ids:
            self.sanity_comment = "sentence cannot be empty"
            return False
        if '' in ids or None in ids:
            self.sanity_comment = "every node must have an id"
            return False
        if len(ids) != len(set(ids)):
            self.sanity_comment = "ids must be unique"
            return False
        tree_ids = [n.id() for n in self.sequence if n.id().in_tree()]
        heads = [n.sdata('head') for n in self.sequence if n.id().in_tree()]
        if '' in heads:
            self.sanity_comment = "can't build a tree without heads"
            return False
        roots = [h for h in heads if h == '0']
        if len(roots) != 1:
            self.sanity_comment = "tree must have exactly one root"
            return False
        heads = set(roots)
        heads.remove('0')
        if not heads.issubset(tree_ids):
            self.sanity_comment = "heads must point to existing nodes"
            return False
        return True

    def build_tree(self):
        children_dict = defaultdict(list)
        for node in self.sequence:
            if not node.id().in_tree():
                node.parent = self # parent is sentence
                continue
            head = node.sdata('head')
            if head == '0':
                self.root = node
                self.root.parent = self
            else:
                children_dict[head].append(node)
        for head_id, children in children_dict.items():
            self._id_dict[head_id].set_children(children)

    def projection(self) -> List[Tree]:
        return self.root.projection()

    def __bool__(self):
        return self._is_good
    def get_node(self, id : str) -> Tree|None:
        id = NodeID(id)
        return self._id_dict.get(id)

    def search(self, src: str|Search) -> List[Tree]|List[Match]:
        if isinstance(src, str):
            src = Search(src)
        return src.match(self.root)

    def __str__(self):
        text = self.text if self.text else ' '.join([n.sdata('form') for n in self.sequence])
        return text + (' (sent_id=%s)' % self.sent_id)

    def __repr__(self):
        return str(self)

class Doc(List[Sentence]):
    def __init__(self, sentences : List[Sentence]):
        super().__init__(sentences)
        self._id_dict : Dict[str, Sentence] = {s.sent_id : s for s in self}
        if len(self._id_dict) != len(self):
            warnings.warn('Warning! Sentence ids not unique!')

    def __add__(self, other : List[Sentence]) -> Doc:
        return Doc(list(self) + list(other))

    def __iadd__(self, other) -> Doc:
        self.__init__(list(self) + list(other))
        return self

    def get_sentence(self, sent_id) -> Sentence|None:
        return self._id_dict.get(sent_id)

    def get_node(self, uid : str) -> Tree|None:
        if Tree.UID_SEPARATOR not in uid:
            raise Exception('Invalid uid "%s"' % str(uid))
        sent_id, node_id = uid.rsplit(Tree.UID_SEPARATOR, 1)
        sentence = self.get_sentence(sent_id)
        if sentence is None:
            return None
        node = sentence.get_node(node_id)
        return node

    def compare_uids(self, uid1 : str, uid2 : str) -> int:
        if Tree.UID_SEPARATOR not in uid1 or Tree.UID_SEPARATOR not in uid2:
            raise Exception('Invalid uids "%s", "%s"' % (str(uid1), str(uid2)))
        if uid1 == uid2:
            return 0
        sent_id1, node_id1 = uid1.rsplit(Tree.UID_SEPARATOR, 1)
        sent_id2, node_id2 = uid2.rsplit(Tree.UID_SEPARATOR, 1)
        if sent_id1 == sent_id2:
            node_id1 = NodeID(node_id1)
            node_id2 = NodeID(node_id2)
            return -1 if node_id1 < node_id2 else 1
        sent1_index = self.index(self.get_sentence(sent_id1))
        sent2_index = self.index(self.get_sentence(sent_id2))
        return -1 if sent1_index < sent2_index else 1

    def iter_nodes(self, from_node : Tree = None, **kwargs) -> Generator[Tree, None, None]:
        start_sentence = from_node.sentence() if from_node else self[0]
        try:
            start_index = self.index(start_sentence)
        except:
            raise Exception('Could not find sentence %s containing node %s is doc' % (str(from_node), str(start_sentence)))
        for sentence in self[start_index:]:
            for node in sentence.iter_nodes(from_node, **kwargs):
                yield node
            from_node = None

    def search(self, src: str|Search) -> Generator[Tree|Match, None, None]:
        for sentence in self:
            for match in sentence.search(src):
                yield match

    @staticmethod
    def from_conllu(filename : str) -> Doc:
        return Doc(conllu_path.iter_sentences_from_conllu(filename))

    def to_conllu(self, filename : str = None) -> str|None:
        buffer = ''
        fptr = open(filename, 'w', encoding='utf-8') if filename else None
        for sentence in self:
            if fptr:
                fptr.write(conllu_path.conllu.sentence_to_conllu(sentence))
            else:
                buffer += conllu_path.conllu.sentence_to_conllu(sentence)
        if fptr:
            fptr.close()
        else:
            return buffer
