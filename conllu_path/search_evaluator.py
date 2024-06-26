from __future__ import annotations

from enum import Enum
from typing import Iterable, Set, List

from conllu_path import Tree

import re

from conllu_path.tree import FIXED_EXPR_LEMMA_KEY

REGEX_DELIM_START = '{'
REGEX_DELIM_STOP = '}'

class Evaluator:
    def evaluate(self, node : Tree) -> bool:
        pass

class ConstantEvaluator(Evaluator):
    def __init__(self, value : bool):
        self._value = value
    def evaluate(self, node : Tree) -> bool:
        return self._value

class ValueComparer(Evaluator):
    def __init__(self, operator : str, key : str, values : Iterable[str]):
        self.operator = operator
        self.key = key
        self.values = set(values)
        values_str = '|'.join(self.values)
        if (values_str.startswith(REGEX_DELIM_START)
                and values_str.endswith(REGEX_DELIM_STOP)):
            values_str = values_str[len(REGEX_DELIM_START):-(len(REGEX_DELIM_STOP))] # strip delimiters
        try:
            self.regex = re.compile(values_str)
        except Exception as e:
            raise Exception('Error in regex %s: %s' % (values_str, str(e)))

    def evaluate(self, node : Tree) -> bool:
        actual_values = node.sdata(self.key) if self.key == [FIXED_EXPR_LEMMA_KEY]\
            else node.data(self.key)
        if isinstance(actual_values, str):
            actual_values = {actual_values}
        elif isinstance(actual_values, Iterable):
            actual_values = set(actual_values)
        else: # unknown type of value or None -- don't add
            return False
        # return bool(self.values.intersection(actual_values))
        if self.operator == '=':
            return any([self.regex.fullmatch(v) for v in actual_values])
        else: # operator '~'
            return any([self.regex.search(v) for v in actual_values])
    def __str__(self):
        return '.'.join(self.key) + self.operator + ','.join(self.values)
    def __repr__(self):
        return self.__str__()

class Operator(Enum):
    AND = '&'
    OR = '|'
    NOT = '!'

_op_dict = {
    Operator.AND: lambda a,b : a and b,
    Operator.OR: lambda a,b: a or b,
    Operator.NOT: lambda a,b : not a
}

class Operation(Evaluator):
    def __init__(self, operator: Operator, left: Evaluator, right: Evaluator = None):
        self.operator = operator
        self.left = left
        self.right = right
    def evaluate(self, node : Tree) -> bool:
        left_val = self.left.evaluate(node)
        right_val = self.right.evaluate(node) if self.right else None
        return _op_dict[self.operator](left_val, right_val)
    def __str__(self):
        return str(self.operator.value) + '(' + self.left.__str__() + (' ' + self.right.__str__() if self.right else '') + ')'
    def __repr__(self):
        return str(self)


class NodePathEvaluator(Evaluator):
    def __init__(self, path_type : str, evaluator : Evaluator):
        self.path_type = path_type
        self.evaluator = evaluator
        self.matching_nodes = []
        self.non_matching_nodes = []
    def evaluate(self, node : Tree) -> bool:
        if self.path_type == '../': # parent
            node_list = [node.parent] if node.parent else []
        elif self.path_type == '/': # children
            node_list = node.children()
        elif self.path_type == '//': # all descendants
            node_list = [c for c in node.traverse() if c is not node]
        elif self.path_type == './': # children plus self
            node_list = [node] + node.children()
        elif self.path_type == './/': # all descendants plus self
            node_list = list(node.traverse())
        elif self.path_type == '.': # current head_node
            node_list = [node]
        elif self.path_type == '<':
            node_list = node.before() #[child for child in node.children() if before(child, node)]
        elif self.path_type == '>':
            node_list = node.after() #[child for child in node.children() if not before(child, node)]
        else:
            raise Exception("Unknown path " + str(self.path_type))
        self.matching_nodes = [n for n in node_list if self.evaluator.evaluate(n)]
        self.non_matching_nodes = [n for n in node_list if n not in self.matching_nodes]
        return bool(self.matching_nodes)

    def __str__(self):
        return self.path_type + '[' + self.evaluator.__str__() + ']'
    def __repr__(self):
        return self.__str__()

