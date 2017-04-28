# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import unicode_literals

import collections


class TypedList(collections.MutableSequence):
    """A ``list``-like object with one or more specified Type(s)
    
    Implements all methods and operations of
    ``collections.MutableSequence`` as well as dict's ``copy``. Also
    provides for Type validation against provided Type(s) ``lower_items``.
    
    """

    def __init__(self, validtypes, *args):
        # type: (object, object) -> None
        """

        :param validtypes: Provide a type for this TypedList object
        :param args: 
        """
        self.validtypes = validtypes
        self.list = list()
        self.extend(list(args))

    def validate_type(self, value):
        if not isinstance(value, self.validtypes):
            raise TypeError(value)

    def __getitem__(self, key):
        return self.list[key]

    def __setitem__(self, key, value):
        self.validate_type(value)
        self.list[key] = value

    def __delitem__(self, key):
        del self.list[key]

    def __len__(self):
        return len(self.list)

    def insert(self, key, value):
        self.validate_type(value)
        self.list.insert(key, value)

    def __str__(self):
        return str(self.list)