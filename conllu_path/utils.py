from typing import Iterator, Callable, Iterable

from conllu_path.tree import Tree

def _default_node_to_word(node : Tree, all_spaces : bool = False) -> str:
    return (node.sdata('form') +
            ('' if not all_spaces and node.sdata('misc.SpaceAfter') == 'No' else ' '))


def sequence_to_string(node_sequence : Iterable[Tree],
                       node_to_word_fn : Callable[[Tree], str] = None,
                       **kwargs) -> str:
    all_space_flag = bool(kwargs.get('all_spaces'))
    node_to_word_fn = _default_node_to_word if node_to_word_fn is None else node_to_word_fn
    return ''.join([node_to_word_fn(n, all_space_flag) for n in node_sequence])

