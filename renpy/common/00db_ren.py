# Copyright 2004-2022 Tom Rothamel <pytom@bishoujo.us>
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import renpy.config as config
import renpy.exports as renpy

"""renpy
init -1100 python:
"""

class JSONDB(object):
    """
    :doc: jsondb

    Creates a JSONDB object, a dictionary-like object that persists
    its data to a JSON file.

    This is intended to be used by game developers to store data in a
    database that can be version-controlled as part of the game script.
    For example, this can store information associated with each
    say statement, that can change how a say statement is displayed.

    JSONDBs are not intended for data that is changed after the game
    has been released. :doc:`persistent` or normal save files are
    better choices for that data.

    The database should only contain data that Python can serialize to
    JSON. This includes lists, dictionaries (with strings as keys),
    strings, numbers, True, False, and None.

    A JSONDB can accept a key, either one generated by Ren'Py, or one
    returned by a function. The key must be a string. The contents of
    the database are determined by the key that is in effect when the
    JSONDB is accessed. For example, when keyed by dialogue, there is
    a different key for each line of dialogue that is displayed.

    A JSONDB should be created during init (in an init python block or
    define statement), and will automatically be saved to the disk provided
    at least one key in the dictionary is set. For example::

        define balloonData = JSONDB("balloon.json", key="dialogue", default={ "enabled" : False })

    JSONDBs can, in most circumstances, be used like dictionaries. For
    example::

        screen say(who, what):
            if balloonData["enabled"]:
                use balloon_say(who, what)
            else:
                use adv_say(who, what)

            if config.developer:
                textbutton "Dialogue Balloon Mode":
                    action ToggleDict(balloonData, "enabled")

    The JSONDB constructor takes the following arguments:

    `filename`
        The filename the database is stored in. This is relative to the
        game directory. It's recommended that the filename end in ".json".

    `key`
        Determines the key used to index the database. If this is None, then
        the default key of "data" is used. If this is the string "dialogue",
        the translation identifier (which is unique for each line of dialogue,
        and also used for automatic voicing) is used. Otherwise, this should
        be a function, that is called to return the key.

    `default`
        If this is not None, it should be a dictionary. When a new key is
        accessed, this object is shallow copied, and the contents is placed
        into the JSONDB.
    """


    def __init__(self, filename, key=None, default=None):

        if not renpy.is_init_phase():
            raise Exception("JSONDBs can only be created during init.")

        # The filename the database is stored in.
        self.fn = filename

        # The data contained in the database.
        self.data = { }

        # The default contents of the database.
        if default is not None:
            self.default = default.copy()
        else:
            self.default = { }

        # True if an data has been changed after the databse was loaded.
        self.dirty = False

        # Either a key function to use to index the database, or None to
        # use the standard key of 'data'.
        if key == "dialogue":
            self.key = self.dialogue_key
        else:
            self.key = key

        # Schedule the database to be saved when the game quits.
        config.at_exit_callbacks.append(self.save)

        # Load the database.
        import json

        if not renpy.loadable(self.fn):
            return

        with renpy.open_file(self.fn, "utf-8") as f:
            self.data = json.load(f)

    def dialogue_key(self):
        return renpy.get_translation_identifier()

    def save(self):

        if not self.dirty:
            return

        import os, json

        fn = os.path.join(config.gamedir, self.fn)

        with open(fn + ".new", "w") as f:
            json.dump(self.data, f, indent=4, sort_keys=True)

        try:
            os.rename(fn + ".new", fn)
        except Exception:
            os.remove(fn)
            os.rename(fn + ".new", fn)

        self.dirty = False

    def check(self, value):
        if not config.developer:
            raise RuntimeError("A JSONDB can only be modified when config.developer is True.")

        import json

        try:
            json.dumps(value)
        except:
            raise TypeError("The data {!r} is not JSON serializable.".format(value))

    def get_dict(self):
        if self.key is not None:
            key = self.key()
        else:
            key = 'data'

        if key is None:
            if config.developer:
                raise Exception("Accessing JSONDB {} with a None key.".format(self.fn))

        if key not in self.data:
            self.data[key] = self.default.copy()

        return self.data[key]

    def __iter__(self):
        return iter(self.get_dict())

    def __len__(self):
        return len(self.get_dict())

    def __getitem__(self, key):
        return self.get_dict()[key]

    def __setitem__(self, key, value):
        self.check(value)
        self.get_dict()[key] = value
        self.dirty = True

    def __delitem__(self, key):
        self.dirty = True
        del self.get_dict()[key]

    def __contains__(self, key):
        return key in self.get_dict()

    def clear(self):
        self.dirty = True
        self.get_dict().clear()

    def copy(self):
        return self.get_dict().copy()

    def has_key(self, key):
        return key in self.get_dict()

    def get(self, key, default=None):
        return self.get_dict().get(key, default)

    def items(self):
        return self.get_dict().items()

    def keys(self):
        return self.get_dict().keys()

    def pop(self, key, default=None):
        self.dirty = True
        return self.get_dict().pop(key, default)

    def popitem(self):
        self.dirty = True
        return self.get_dict().popitem()

    def reversed(self):
        return self.get_dict().reversed()

    def setdefault(self, key, default=None):

        d = self.get_dict()
        if key not in d:
            self.check(default)
            self.dirty = True

        return d.setdefault(key, default)

    def update(self, *args, **kwargs):
        self.dirty = True

        d = dict()
        d.update(*args, **kwargs)
        self.check(d)

        self.get_dict().update(d)

    def values(self):
        return self.get_dict().values()

    def __ior__(self, other):
        self.dirty = True
        self.get_dict().update(other)
        return self

    def __eq__(self, other):
        return self.get_dict() == other

    def __ne__(self, other):
        return self.get_dict() != other

    def __le__(self, other):
        return self.get_dict() <= other

    def __lt__(self, other):
        return self.get_dict() < other

    def __ge__(self, other):
        return self.get_dict() >= other

    def __gt__(self, other):
        return self.get_dict() > other

    def __repr__(self):
        d = self.get_dict()
        return "<JSONDB {!r} {!r}>".format(self.fn, d)

    def __reversed__(self):
        return reversed(self.get_dict())