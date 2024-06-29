from typing import List

import lark
from conllu_path.search_evaluator import Evaluator, ValueComparer, ConstantEvaluator, NodePathEvaluator, Operation, Operator
from conllu_path.search_evaluator import REGEX_DELIM_STOP, REGEX_DELIM_START

grammar = r"""

node_list   : head_node
            | node_list head_node 

head_node   : PATH_MARKER token

token   : "[" or_expr "]"

or_expr : or_expr "|" or_expr
        | and_expr
        
and_expr    : and_expr "&" and_expr
            | and_expr and_expr        //same as &
            | equality
            
equality    : key EQU values
            | "(" or_expr ")" 
            | negated_equality 
            | head_node
            | any

negated_equality : "!" equality

any : "*"

values : values "," WORD
        | WORD
        | REGEX

key     : key "." CNAME
        | CNAME

PATH_MARKER : "/" | "//" | "./" |  "../" | ".//" | "." | "<" | ">"
EQU : "=" | "~"
WORD: /[\w\-\'][\w\-\:\.\-\']*/
REGEX : "{regex_start}" /.+/ "{regex_stop}"

%import common.CNAME
%import common.ESCAPED_STRING
%import common.WS_INLINE
%ignore WS_INLINE

""".format(regex_start=REGEX_DELIM_START, regex_stop=REGEX_DELIM_STOP)
class ExpressionBuilder(lark.Transformer):
    def node_list(self, args):
        if len(args) == 1:
            return [args[0]]
        return args[0] + [args[1]]
    def head_node(self, args):
        return NodePathEvaluator(args[0].value, args[1])
    def token(self, args):
        return args[0]
    def or_expr(self, args):
        if len(args) == 1: return args[0]
        return Operation(Operator.OR, args[0], args[1])
    def and_expr(self, args):
        if len(args) == 1: return args[0]
        return Operation(Operator.AND, args[0], args[1])
    def equality(self, args):
        if len(args) == 1: return args[0]
        return ValueComparer(args[1], args[0], args[2]) # '='
    def negated_equality(self, args):
        return Operation(Operator.NOT, args[0])
    def any(self, args):
        return ConstantEvaluator(True)
    def values(self, args):
        if len(args) == 1:
            return [args[0].value]
        return args[0] + [args[1].value]
    def key(self, args):
        if len(args) == 1:
            return [args[0].value]
        return args[0] + [args[1].value]

_parser = lark.Lark(grammar, start="node_list", parser="lalr", transformer=ExpressionBuilder())

def parse_evaluator(expr : str) -> List[NodePathEvaluator]:
    try:
        return _parser.parse(expr)
    except lark.UnexpectedInput as unex_input_e:
        index = unex_input_e.column
        e_with_error = expr[:index] + 'ˇ' + expr[index:]
        e_string = 'Error in expression "%s" at character %d ("%s")' % (e_with_error, index, expr[unex_input_e.column-1])
        for op, cp in [('(', ')'), ('[', ']'), ('{', '}')]:
            if expr.count(op) != expr.count(cp):
                e_string += '\nUnequal number of %s and %s' % (op, cp)
        e = Exception(e_string)
        raise e from None
    except Exception as e:
        raise Exception(str(e))
