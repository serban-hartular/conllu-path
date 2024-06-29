from __future__ import annotations

import abc
from typing import List, Set, Dict

class AssignException(Exception):
    pass

class NodeData(abc.ABC):
    """Abstract class for accessing the nested dict that holds node data.

    Since the implementation of the node data may vary, use the data(),
    sdata() and assign() functions declared here to read or change node data.

    Attributes:
        PATH_SEPARATOR:
            String used to separate keys when the path to the data is a string
            rather than a list of strings.
    """
    PATH_SEPARATOR = '.'
    @abc.abstractmethod
    def data(self, path: str | List[str] = None) -> NodeData | Set | str | None:
        """Returns data specified by path arg

        Given a path consisting of a sequence of keys (e.g. ['key1', 'key2', 'key3'],)
        returns the data pointed to by this path of keys, i.e.
        data['key1']['key2']['key3'], where data is a dict.

        Args:
            path:
                Sequence of keys that leads to the desired data. Can be a
                list of strings or a string with the keys separated by the
                PATH_SEPARATOR class attribute (a period by default).

        Returns:
            None if the path doesn't point to data, else the data, which can be
            a set, a string, or another instance of NodeData.
        """
        pass
    def sdata(self, path: str | List[str] = None) -> str:
        """Returns data specified by path arg in string form

        see the data() function for details

        Returns:
            The data pointed to by the path in string form.
            If the data is None, returns an empty string.
            If the data is a set, returns its contents joined by commas.
            If the data is an instance of NodeData, returns its representation as a dict
            If the data is a string, returns that string
        """
        v = self.data(path)
        if v is None: return ''
        if isinstance(v, str): return v
        if isinstance(v, NodeData): return str(v.to_dict())
        return ','.join([str(i) for i in v])
    @abc.abstractmethod
    def assign(self, path: str|List[str], value : NodeData|Set|str) -> bool:
        """Assigns a value to the data indicated by the path

        Given a path consisting of a sequence of keys (e.g. ['key1', 'key2', 'key3'],
        assigns a value to the data pointed to by this path of keys, i.e.
        data['key1']['key2']['key3'] = value, where data is a dict. If the dict
        indicated by the path does not exist, it does nothing and returns False.

        Args:
            path:
                Sequence of keys that leads to the desired data. Can be a
                list of strings or a string with the keys separated by the
                PATH_SEPARATOR class attribute (a period by default).

            value:
                Value to be assigned. Can be a string, a set of strings, or
                an instance of NodeData.
        Returns:
            False if the path doesn't point to data, else True.
        """
        pass
    @abc.abstractmethod
    def keys(self) -> List[str]:
        """Returns the keys present in the underlying dict."""
        pass
    @abc.abstractmethod
    def to_dict(self) -> Dict[str, NodeData | Set | str | None]:
        """Returns self as a nested dict."""
        pass
    def __str__(self):
        return str(self.to_dict())
    def __repr__(self):
        return str(self)

class DictNode(NodeData):
    """Generic implementation of NodeData. Underlying data is a dict."""
    def __init__(self, d : Dict):
        self._ddict = dict(d)

    def keys(self) -> List[str]:
        return list(self._ddict.keys())
    def to_dict(self) -> Dict:
        return dict(self._ddict)
    def data(self, path: str | List[str] = None) -> NodeData | Set[str] | str | None:
        if isinstance(path, str):
            path = path.split(NodeData.PATH_SEPARATOR)
        if not path:
            return self
        v = self._ddict.get(path[0])
        if v is None: return None
        if isinstance(v, NodeData):
            return v.data(path[1:])
        if len(path) == 1:
            return v
        return None

    def assign(self, path: str|List[str], value: NodeData | Set | str) -> bool:
        if isinstance(path, str):
            path = path.split(NodeData.PATH_SEPARATOR)
        if len(path) == 1:
            # if path[0] in self._ddict: # allow adding data
            self._ddict[path[0]] = value
            return True
        v = self.data(path[:-1])
        if isinstance(v, NodeData):
            v.assign([path[-1]], value)
            return True
        raise AssignException('In path "%s": path "%s" does not point to dict-like data.' %
                              ('.'.join(path), '.'.join(path[:-1])))

class FixedKeysNode(NodeData):
    """Implementation of NodeData where the keys are fixed and known. """
    def __init__(self, l : List[DictNode | Set | str | None],
                 key_index_dict : Dict[str, int]):
        self._dlist = l
        self.key_index_dict = key_index_dict
        if min(self.key_index_dict.values()) < 0:
            raise Exception('Negative index in key_index_dict')
        if max(self.key_index_dict.values()) > len(self._dlist) - 1:
            self._dlist.extend([None]*(max(self.key_index_dict.values()) - (len(self._dlist) - 1)))

    def keys(self) -> List[str]:
        return list(self.key_index_dict.keys())
    def to_dict(self) -> Dict:
        return {k: (self._dlist[i].to_dict() if isinstance(self._dlist[i], NodeData) else self._dlist[i])
                for k, i in self.key_index_dict.items()}
    def data(self, path: str | List[str] = None) -> NodeData | Set | str | None:
        if isinstance(path, str):
            path = path.split(NodeData.PATH_SEPARATOR)
        if not path:
            return self
        v = self._dlist[self.key_index_dict[path[0]]] if path[0] in self.key_index_dict else None
        if v is None: return None
        if isinstance(v, NodeData):
            return v.data(path[1:])
        if len(path) == 1:
            return v
        return None

    def assign(self, path: str | List[str], value: NodeData | Set | str) -> bool:
        if isinstance(path, str):
            path = path.split(NodeData.PATH_SEPARATOR)
        if len(path) == 1:
            if path[0] in self.key_index_dict:
                self._dlist[self.key_index_dict[path[0]]] = value
                return True
            raise AssignException('Key %s does not exist!' % path[0])
        v = self.data(path[:-1])
        if isinstance(v, NodeData):
            v.assign([path[-1]], value)
            return True
        raise AssignException('In path "%s": "%s" does not point to dict-like data.' %
                        ('.'.join(path), '.'.join(path[:-1])))
