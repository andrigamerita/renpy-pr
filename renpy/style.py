# Copyright 2004-2007 PyTom <pytom@bishoujo.us>
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

import renpy

# A list of roles we know about.
roles = [ 'selected_', '' ]

# A list of style prefixes we care about, including no prefix.
prefixes = [ 'hover_', 'idle_', 'insensitive_', 'activate_', ]

# A map from prefix to priority and alternates.
prefix_subs = { }

def register_prefix(prefix, prio, addprefixes=[]):

    for r in roles:
        if r and prefix.startswith(r):
            alts1 = [ r ]
            break
    else:
        alts1 = roles

    for p in prefixes:
        if prefix.endswith(p):
            alts2 = [ p ]
            break
    else:
        alts2 = prefixes

    alts2 += addprefixes
        
    alts = [ a1 + a2 for a1 in alts1 for a2 in alts2 ]

    prefix_subs[prefix] = prio, alts


register_prefix('selected_activate_', 6)
register_prefix('selected_hover_', 5, [ 'activate_' ])
register_prefix('selected_idle_', 5)
register_prefix('selected_insensitive_', 5)
register_prefix('selected_', 4)
register_prefix('activate_', 3)
register_prefix('hover_', 2, [ 'activate_' ])
register_prefix('idle_', 2)
register_prefix('insensitive_', 2)
register_prefix('', 1)

# A map of properties that we know about. The properties may take a
# function that is called on the argument.
style_properties = dict(
    antialias = None,
    background = renpy.easy.displayable,
    bar_invert = None,
    bar_vertical = None,
    black_color = renpy.easy.color,
    bold = None,
    bottom_bar = renpy.easy.displayable,
    bottom_gutter = None,
    bottom_margin = None,
    bottom_padding = None,
    box_first_spacing = None,
    box_layout = None,
    box_spacing = None,
    clipping = None,
    color = renpy.easy.color,
    drop_shadow = None,
    drop_shadow_color = renpy.easy.color,
    enable_hover = None, # Doesn't do anything anymore.
    first_indent = None,
    focus_mask = None,
    focus_rect = None,
    font = None,
    sound = None,
    italic = None,
    initial_time_offset = None,
    layout = None,
    left_bar = renpy.easy.displayable,
    left_gutter = None,
    left_margin = None,
    left_padding = None,
    line_spacing = None,
    min_width = None,
    rest_indent = None,
    right_bar = renpy.easy.displayable,
    right_gutter = None,
    right_margin = None,
    right_padding = None,
    size = None,
    slow_abortable = None,
    slow_cps = None,
    slow_cps_multiplier = None,
    subtitle_width = None,
    text_y_fudge = None,
    text_align = None,
    thumb = renpy.easy.displayable,
    thumb_offset = None,
    thumb_shadow = renpy.easy.displayable,
    top_bar = renpy.easy.displayable,
    top_gutter = None,
    top_margin = None,
    top_padding = None,
    underline = None,
    xanchor = None,
    xfill = None,
    xmaximum = None,
    xminimum = None,
    xoffset = None,
    xpos = None,
    yanchor = None,
    yfill = None,
    ymaximum = None,
    yminimum = None,
    yoffset = None,
    ypos = None,
    )

substitutes = dict(
    xmargin = [ 'left_margin', 'right_margin' ],
    ymargin = [ 'top_margin', 'bottom_margin' ],
    xalign = [ 'xpos', 'xanchor' ],
    yalign = [ 'ypos', 'yanchor' ],
    xpadding = [ 'left_padding', 'right_padding' ],
    ypadding = [ 'top_padding', 'bottom_padding' ],
    minwidth = [ 'min_width' ],
    textalign = [ 'text_align' ],
    slow_speed = [ 'slow_cps' ],
    )

# Map from property to number.
property_number = { }

# Map from prefix to offset.
prefix_offset = { }

# Map from prefix_property to a list of priorities, offset numbers, and functions.
expansions = { }

# The total number of property numbers out there.
property_numbers = 0

# This is a function, to prevent namespace pollution. It's called
# once at module load time.
def init():

    global property_numbers
    
    # Figure out a map from style property name to an (arbitrary,
    # session-specific) style property number.
    for i, p in enumerate(style_properties):
        property_number[p] = i

    # Figure out a map from style prefix to style property number offset.
    property_numbers = 0    
    for r in roles:
        for p in prefixes:
            prefix_offset[r + p] = property_numbers
            property_numbers += len(style_properties)

    # Figure out the mappings from prefixed properties to expansions of
    # those properties.
    for prefix, (prio, alts) in prefix_subs.iteritems():

        for prop, propn in property_number.iteritems():
            func = style_properties[prop]
            expansions[prefix + prop] = [ (prio, propn + prefix_offset[a], func) for a in alts ]

    # Expand out substitutes.
    for k in substitutes.keys():
        for p in prefixes + [ '' ]:
            expansions[p + k] = [ a for b in substitutes[k] for a in expansions[p + b] ]
        
            
init()

# A map from a style name to the style associated with that name.
style_map = { }

# A map from a style name to the style proxy associated with that name.
style_proxy_map = { }

# True if we have expanded all of the style caches, False otherwise.
styles_built = False

# A list of styles that are pending expansion.
styles_pending = [ ]

def reset():
    """
    This resets all of the data structures associated with style
    management.
    """

    global style_map
    global styles_built
    global styles_pending
    global style_info 
    
    style_map = { }
    styles_built = False
    styles_pending = [ ]

class StyleManager(object):
    """
    This is the singleton object that is exported into the store
    as style
    """

    def __getattr__(self, name):
        try:
            return style_map[name]
        except:
            raise Exception('The style %s does not exist.' % name)

    def create(self, name, parent, description=None):
        """
        Creates a new style.

        @param name: The name of the new style, as a string.

        @param parent: The parent of the new style, as a string. This
        is either 'default' or something more specific.

        @param description: A description of the style, for
        documentation purposes.
        """

        s = Style(parent, { }, heavy=True)        
        style_map[name] = s
        s.name = name
        
    def exists(self, name):
        """
        This determines if the named style exists.
        """
        
        return name in style_map

def expand_properties(properties):

    rv = [ ]
    cache = { }
    
    for prop, val in properties.iteritems():

        if cache:
            cache.clear()

        try:
            e = expansions[prop]
        except KeyError:
            raise Exception("Style property %s is unknown." % prop)

        for prio, propn, func in e:

            if func:
                idval = id(val)
                
                if idval in cache:
                    newval = cache[idval]
                else:
                    newval = func(val)
                    cache[idval] = newval

            else:
                newval = val
                    
            rv.append((prio, propn, newval))

    # Places things in priority order... so more important properties
    # come last.
    rv.sort()
    return rv



# This builds the style. If recurse is True, this also builds the
# parent style.
def build_style(style):

    if not style.heavy:
        return
    
    # This is a list of light styles, which don't have a cache. This
    # also includes the current style as the last entry, since we haven't
    # built the cache for it yet.
    light_styles = [ ]

    s = style
    
    while s:
        
        light_styles.insert(0, s)       

        parent = s.parent
        
        # No parent... we're done.
        if parent is None:
            break

        # Otherwise, parent is a string. Turn it into a Style object.    
        try:
            parent = style_map[parent]
        except:
            try:
                parent = getattr(renpy.game.style, parent)

            except:
                raise Exception('Style %s is not known.' % style.parent)

        # If the parent is heavy, get out of here.
        if parent.heavy:
            break

        # Otherwise, recurse.
        s = parent

    if parent:

        # This will only build a heavy style.
        if not parent.cache:
            build_style(parent)

        cache = parent.cache[:]

    else:
        cache = [ None ] * property_numbers

    # For speed, make this local.
    e = expansions

    for s in light_styles:
        for p in s.properties:
            for prio, propn, val in expand_properties(p):
                cache[propn] = val

    style.cache = cache

                
# This builds all pending styles, recursing to ensure that they are built
# in the right order.
def build_styles():

    global styles_pending
    global styles_built

    for s in styles_pending:
        build_style(s)

    styles_pending = None
    styles_built = True

def rebuild():

    global style_pending
    global styles_built

    styles_pending = [ i for i in style_map.values() if i.heavy ]
    styles_built = False
    
    for i in styles_pending:
        i.__dict__["cache"] = { }

    build_styles()

def backup():
    rv = { }
    
    for k, v in style_map.iteritems():
        rv[k] = v.properties[:]

    return rv
        
def restore(o):
    global styles_built
    global styles_pending
    
    styles_pending = [ ]
    styles_built = False

    for k, v in o.iteritems():
        style_map[k].properties = v
        styles_pending.append(style_map[k])

def style_metaclass(name, bases, attrs):

    for k in expansions.iterkeys():
        def setter(self, v,  k=k):
            self.setattr(k, v)

        def deleter(self, k=k):
            self.delattr(k)

        attrs[k] = property(None, setter, deleter)
    
    for k, number in property_number.iteritems():
        def getter(self, number=number):
            return self.cache[self.offset + number]

        def setter(self, v,  k=k):
            self.setattr(k, v)

        def deleter(self, k=k):
            self.delattr(k)

        attrs[k] = property(getter, setter, deleter)

    return type(name, bases, attrs)


# This class is used for heavyweight and lightweight styles. (Heavyweight
# styles have a class, lightweight styles do not.)
class Style(object):

    __metaclass__ = style_metaclass
    __slots__ = [
        'cache',
        'properties',
        'offset',
        'prefix',
        'heavy',
        'name',
        'help',
        'parent',
        ]

    
    def __getstate__(self):

        rv = dict(vars(self))

        del rv["cache"]
        del rv["offset"]

        return rv

    def __setstate__(self, state):

        for k, v in state.iteritems():
            setattr(self, k, v)

        self.cache = [ ]
        self.offset = prefix_offset[self.prefix]

        build_style(self)

    def __init__(self, parent, properties=None, heavy=False, name=None, help=None):

        self.prefix = 'insensitive_'
        self.offset = prefix_offset['insensitive_']

        self.heavy = heavy
        self.name = name
        
        if parent and not isinstance(parent, basestring):
            parent = parent.name
            if parent is None:
                raise Exception("The parent of a style must be a named style.")
            
        self.parent = parent

        self.cache = None
        self.properties = [ ]

        if properties:
            self.properties.append(properties)
            
            # for prio, prop, val in expand_properties(properties):
            #    self.properties[prop] = val

        if styles_built:
            build_style(self)
        else:
            styles_pending.append(self)

    def set_prefix(self, prefix):
        self.prefix = prefix
        self.offset = prefix_offset[prefix]
            
    def setattr(self, name, value):

        self.properties.append({ name : value })
 
        if styles_built:
            build_style(self)

    def delattr(self, name):

        for p in self.properties:
            if name in p:
                del p[name]
        
    def clear(self):
        if styles_built:
            raise Exception("Cannot clear a style after styles have been built.")
        else:
            self.properties = [ ]
            
    def take(self, other):

        self.properties = other.properties[:]

        if styles_built:
            build_style(self)

    def setdefault(self, **properties):
        """
        This sets the default value of the given properties, if no more
        explicit values have been set.
        """

        for p in self.properties:
            for k in p:
                if k in properties:
                    del properties[k]

        if properties:
            self.properties.append(properties)


def write_text(filename):

    f = file(filename, "w")

    styles = style_map.items()
    styles.sort()

    for name, sty in styles:

        print >>f, name, "inherits from", sty.parent

        props = [ (prefix + prop, sty.cache[prefixn + propn])
                  for prefix, prefixn in prefix_offset.iteritems()
                  for prop, propn in property_number.iteritems() ]

        props.sort()

        for prop, val in props:

            pname = name

            while pname:
                psty = style_map[pname]

                if prop in psty.properties:
                    break
                else:
                    pname = psty.parent
 
            if pname != name:
                inherit = "(%s)" % pname
            else:
                inherit = "(****)"

            print >>f, "   ", inherit, prop, "=", repr(val)

        print >>f

    f.close()
        
    
