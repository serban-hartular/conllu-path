from __future__ import annotations

import re
from collections import UserString
from functools import total_ordering

SYNTACTIC_NODE_ID = re.compile(r'[0-9]+(\.[0-9]+)?')
MULTIWORD_NODE_ID = re.compile(r'[0-9]+-[0-9]+')

@total_ordering
class NodeID(UserString):
    def __init__(self, string):
        super().__init__(string)
        self._multiword = False
        self._elided = False
        self._numeric = None
        self.validate()
    def __hash__(self):
        return hash(str(self))
    def __contains__(self, item : 'NodeID'|str):
        if isinstance(item, NodeID): # self a multiword node that contains item?
            return self._multiword and not item._multiword\
                and item._numeric[0] in range(self._numeric[0], self._numeric[1]+1)
        return item in str(self)
    def __lt__(self, other : 'NodeID'):
        if self._numeric[0] == other._numeric[0]:
            if other in self: # self is multimword and contains other
                return True
            return self._numeric[1] < other._numeric[1] # two elided nodes
        return self._numeric[0] < other._numeric[0]
    def __eq__(self, other):
        return str(self) == str(other)
    def __gt__(self, other : 'NodeID'):
        return self != other and not self < other
    # def __le__(self, other):
    #     return not self > other
    # def __ge__(self, other):
    #     return not self < other
    def validate(self):
        if MULTIWORD_NODE_ID.match(str(self)):
            self._multiword = True
            nr0, nr1 = [int(s) for s in self.split('-')]
            self._numeric = (nr0, nr1)
        elif SYNTACTIC_NODE_ID.match(str(self)):
            if '.' in self:
                self._elided = True
                nr0, nr1 = [int(s) for s in self.split('.')]
                self._numeric = (nr0, nr1)
            else:
                self._numeric = (int(self), 0)
        else:
            raise Exception('Invalid id "%s"' % self)
    def elided(self) -> bool:
        return self._elided
    def multiword(self) -> bool:
        return self._multiword
    def in_tree(self) -> bool:
        return not self.multiword() and not self.elided()
