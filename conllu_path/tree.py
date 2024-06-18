from __future__ import annotations

import abc
from typing import Dict, List, Set, Generator

from conllu_path.node_data import NodeData
from conllu_path.node_id import NodeID

class Tree:
    UID_SEPARATOR = '/'
    def __init__(self, id : str|NodeID, data: NodeData, children : List['Tree'] = None, parent : 'Tree' = None):
        self._id = NodeID(id)
        self._data = data
        self._children = []
        self._before = []
        self._after = []
        self.parent = parent
        if children:
            self.set_children(children)
    def id(self) -> NodeID:
        return self._id
    def data(self, path: str | List[str] = None) -> NodeData | Set | str | None:
        return self._data.data(path)
    def sdata(self, path: str | List[str] = None) -> str:
        return self._data.sdata(path)
    def assign(self, path: str|List[str], value : NodeData|Set|str) -> bool:
        return self._data.assign(path, value)
    def keys(self) -> List[str]:
        return self._data.keys()
    def to_dict(self) -> Dict[str, NodeData | Set | str | None]:
        return self._data.to_dict()

    def set_children(self, children : List['Tree']):
        self._children = children
        self._children.sort(key=lambda n : n.id()) # int(n.sdata('id')))
        for child in self._children:
            child.parent = self
        # id = self.id_nr()
        # if id is not None:
        self._before = [n for n in children if n.id() < self.id()]
        self._after = [n for n in children if n.id() > self.id()]
    def children(self) -> List[Tree]:
        return list(self._children)
    def before(self) -> List[Tree]:
        return list(self._before)
    def after(self) -> List[Tree]:
        return list(self._after)

    def traverse(self) -> Generator[Tree, None, None]:
        for child in self.before():
            for node in child.traverse():
                yield node
        yield self
        for child in self.after():
            for node in child.traverse():
                yield node

    def projection(self) -> List[Tree]:
        return list(self.traverse())

    def __str__(self):
        return "%s:%s" % (self.id(), self.sdata('form'))
    def __repr__(self):
        return str(self)

    def sentence(self) -> 'Sentence':
        node = self
        while node.parent and isinstance(node.parent, Tree):
            node = node.parent
        return node.parent

    def uid(self) -> str:
        return self.sentence().sent_id + Tree.UID_SEPARATOR + str(self.id())