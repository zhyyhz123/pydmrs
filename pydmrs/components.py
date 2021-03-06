from collections import namedtuple
try:
    from collections.abc import MutableMapping
except ImportError:  # Python v3.2 or less
    from collections import MutableMapping
from abc import ABCMeta
from functools import total_ordering
from itertools import chain
from warnings import warn

from pydmrs._exceptions import *


@total_ordering
class Pred(object):
    """
    A superclass for all Pred classes.
    Instances of Pred denote a completely underspecified predicate.
    """

    __slots__ = ()  # Suppress __dict__

    def __str__(self):
        """
        Returns 'predsort', the type name for predicates in Delph-in grammars
        """
        return 'predsort'

    def __repr__(self):
        """
        Returns a string representation
        """
        return 'Pred()'

    def __eq__(self, other):
        """
        Checks whether the other object is precisely of type Pred
        """
        return type(other) == Pred

    def __le__(self, other):
        """
        Checks whether the other object is a Pred (including subclasses)
        """
        return isinstance(other, Pred)
    
    @staticmethod
    def normalise_string(string):
        """
        Normalises a predicate string
        """
        # Disallow spaces
        if ' ' in string:
            raise PydmrsValueError('Predicates must not contain spaces')
        # Strip surrounding quotes and disallow other quotes
        if string[0] == '"' and string[-1] == '"':
            string = string[1:-1]
        if string[0] == "'":
            warn('Predicates with opening single-quote have been deprecated', PydmrsDeprecationWarning)
            string = string[1:]
        if '"' in string:
            raise PydmrsValueError('Predicates must not contain quotes')
        # Force lower case
        if not string.islower():
            warn('Predicates must be lower-case', PydmrsWarning)
            string = string.lower()
        # Strip trailing '_rel'
        if string[-4:] == '_rel':
            string = string[:-4]
        
        return string
    
    @classmethod
    def from_string(cls, string):
        """
        Instantiates a pred from a string, normalising as necessary
        """
        normalised = cls.normalise_string(string)
        return cls.from_normalised_string(normalised)

    @staticmethod
    def from_normalised_string(string):
        """
        Instantiates a suitable type of Pred, from a string
        """
        if string[0] == '_':
            return RealPred.from_normalised_string(string)
        else:
            return GPred.from_normalised_string(string)


class RealPred(namedtuple('RealPredNamedTuple', ('lemma', 'pos', 'sense')), Pred):
    """
    Real predicate, with a lemma, part of speech, and (optional) sense.
    All three fields can be underspecified by using '?'.
    The pos can also be underspecified as 'u'.
    The sense can also be underspecified as 'unknown'.
    """

    __slots__ = ()  # Suppress __dict__

    def __new__(cls, lemma, pos, sense=None):
        """
        Create a new instance, allowing the sense to be optional,
        and requiring non-empty lemma and pos
        """
        if not lemma:
            raise PydmrsValueError('a RealPred must have non-empty lemma')
        if not pos:
            raise PydmrsValueError('a RealPred must have non-empty pos')
        if ' ' in lemma or ' ' in pos or (sense and ' ' in sense):
            raise PydmrsValueError('the values of a RealPred must not contain spaces')
        return super().__new__(cls, lemma, pos, sense)

    def __str__(self):
        """
        Return a string, with leading underscore
        """
        if self.sense:
            return "_{}_{}_{}".format(*self)
        else:
            return "_{}_{}".format(*self)

    def __repr__(self):
        """
        Return a string, as "RealPred(lemma, pos, sense)"
        """
        if self.sense:
            return "RealPred({}, {}, {})".format(*(repr(x) for x in self))
        else:
            return "RealPred({}, {})".format(*(repr(x) for x in self))

    def __le__(self, other):
        """
        Checks whether this RealPred underspecifies or equals the other RealPred
        """
        return isinstance(other, RealPred) \
            and (self.lemma == '?' or self.lemma == other.lemma) \
            and (self.pos in ('?', 'u') or self.pos == other.pos) \
            and (self.sense in ('?', 'unknown') or self.sense == other.sense)

    def __lt__(self, other):
        """
        Checks whether this RealPred underspecifies the other RealPred
        """
        return self <= other and self != other

    def __ge__(self, other):
        """
        Checks whether the other RealPred underspecifies or equals this RealPred
        """
        return type(other) == Pred or (isinstance(other, RealPred) and other <= self)

    def __gt__(self, other):
        """
        Checks whether the other RealPred underspecifies this RealPred
        """
        return self >= other and self != other

    @staticmethod
    def from_normalised_string(string):
        """
        Create a new instance from a normalised string.
        :param string: Input string
        :return: RealPred object
        """
        # Require initial underscore
        if string[0] != '_':
            raise PydmrsValueError("RealPred strings must begin with an underscore")
        # Split into 2 or 3 parts
        # This allows the lemma to contain underscores, which sometimes happens in the ERG
        parts = string[1:].rsplit('_', 2)
        # Require at least 2 parts
        if len(parts) < 2:
            raise PydmrsValueError("RealPred strings must have a part of speech separated by an underscore")
        return RealPred(*parts)


class GPred(namedtuple('GPredNamedTuple', ('name')), Pred):
    """
    Grammar predicate, with a rel name.
    The name can be underspecified by using '?'.
    """

    __slots__ = ()  # Suppress __dict__

    def __new__(cls, name):
        """
        Create a new instance, requiring non-empty name
        """
        if not name:
            raise PydmrsValueError('a GPred must have non-empty name')
        return super().__new__(cls, name)

    def __str__(self):
        """
        Return a string
        """
        return str(self.name)

    def __repr__(self):
        """
        Return a string, as "GPred(name)"
        """
        return "GPred({})".format(repr(self.name))

    def __le__(self, other):
        """
        Checks whether this GPred underspecifies or equals the other GPred
        """
        return isinstance(other, GPred) and (self.name == '?' or self.name == other.name)

    def __lt__(self, other):
        """
        Checks whether this GPred underspecifies the other GPred
        """
        return self <= other and self != other

    def __ge__(self, other):
        """
        Checks whether the other GPred underspecifies or equals this GPred
        """
        return type(other) == Pred or (isinstance(other, GPred) and other <= self)

    def __gt__(self, other):
        """
        Checks whether the other GPred underspecifies this GPred
        """
        return self >= other and self != other

    @staticmethod
    def from_normalised_string(string):
        """
        Create a new instance from a normalised string.
        """
        if string[0] == '_':
            raise PydmrsValueError("GPred strings must not begin with an underscore")
        else:
            return GPred(string)


# Sortinfo objects will store features via __slots__
# Users can define subclasses with additional features
# The __slots__ of a class and all its parents are concatenated as the 'features' attribute
# To allow this to happen, we will use a metaclass
# (An alternative solution would be to define a descriptor class, with an instance as a class attribute of Sortinfo)
# (Using a metaclass gives us more freedom - e.g. we can check that subclasses define __slots__)
# This metaclass inherits from ABCMeta rather than type, because MutableMapping has ABCMeta as a metaclass

class SortinfoMeta(ABCMeta):
    """
    A metaclass for Sortinfo, which defines a 'features' class attribute automatically  
    """
    def __new__(mcls, name, bases, namespace):  # @NoSelf - 'mcls' is SortinfoMeta, 'cls' is the new class
        """
        Create a new class, and add a 'features' attribute from __slots__
        """
        # Check that the namespace is compliant
        if '__slots__' not in namespace:
            raise PydmrsError('Subclasses of Sortinfo must define __slots__')
        if 'features' in namespace:
            raise PydmrsError("Subclasses of Sortinfo must not define a 'features' attribute")
        
        # Force all feature names to be lowercase
        namespace['__slots__'] = tuple(feat.lower() for feat in namespace['__slots__'])
        
        # Create the class, and add the 'features' attribute
        cls = super().__new__(mcls, name, bases, namespace)
        cls.features = tuple(chain.from_iterable(getattr(parent, '__slots__', ())
                                                 for parent in reversed(cls.__mro__)))
        
        # Sortinfo defines a from_normalised_dict method which calls either EventSortinfo or InstanceSortinfo
        # Subclasses need to override this method
        if 'from_normalised_dict' not in namespace:
            cls.from_normalised_dict = cls._from_normalised_dict
        
        return cls


class Sortinfo(MutableMapping, metaclass=SortinfoMeta):
    """
    A superclass for all Sortinfo classes.
    Instances of Sortinfo denote completely underspecified sortinfo.
    Subclasses of Sortinfo must specify __slots__ (and optionally, cvarsort)
    """
    __slots__ = ()
    cvarsort = 'i'
    
    # Container methods
    
    def __iter__(self):
        """
        Iterate through all features, including 'cvarsort'
        """
        return chain(('cvarsort',), iter(self.features))
    
    def __len__(self):
        """
        Return the number of features, including 'cvarsort'
        """
        return 1 + len(self.features)
    
    def __contains__(self, feature):
        """
        Check if a feature is present in the class
        """
        return feature == 'cvarsort' or feature in self.features
    
    # For convenience, we can also get features which are not None
    
    def iter_specified(self):
        """
        Return (feature, value) pairs where value is not None, '?', or 'u'
        """
        for feat in self.features:
            val = self[feat]
            if val not in ['?', 'u', None]:
                yield (feat, val)
    
    # Setters and getters
    # Allows both attribute and dictionary access
    # Features and values must all be lowercase
    
    def __setattr__(self, feature, value):
        """
        Set the value of a feature, converting it to lowercase unless it's None
        """
        feature = feature.lower()
        if value is not None:
            value = value.lower()
        super().__setattr__(feature, value)
    
    def __delattr__(self, feature):
        """
        Set the value of a feature to None
        """
        setattr(self, feature, None)
        
    def __setitem__(self, feature, value):
        """
        Set items as attributes
        """
        setattr(self, feature, value)
    
    def __getitem__(self, feature):
        """
        Get the value of a feature, including 'cvarsort'
        """
        feature = feature.lower()
        if feature == 'cvarsort':
            return self.cvarsort
        elif feature in self.features:
            return getattr(self, feature)
        else:
            raise PydmrsKeyError("{} has no feature {}".format(type(self), feature))
    
    def __delitem__(self, feature):
        """
        Set the value of a feature to None
        """
        self[feature] = None
    
    # Initialisation
    
    def __init__(self, *args, **kwargs):
        """
        Initialise values of features, from positional or keyword arguments
        If a feature is not given, its value is set to None
        """
        if len(args) > len(self.features):
            raise PydmrsTypeError("{} takes {} arguments, but {} were given".format(type(self).__name__,
                                                                                    len(self.features),
                                                                                    len(args)))
        for i, value in enumerate(args):
            setattr(self, self.features[i], value)
        for feature, value in kwargs.items():
            setattr(self, feature, value)
        for feature in self.features:
            if not hasattr(self, feature):
                setattr(self, feature, None)

    # Conversion to strings and dicts
    
    def __str__(self):
        """
        Returns a string of the form:
        cvarsort[feature1=value1, feature2=value2, ...]
        """
        spec_feats = ', '.join('{}={}'.format(*pair) for pair in self.iter_specified())
        if spec_feats:
            return '{}[{}]'.format(self.cvarsort, spec_feats)
        else:
            return self.cvarsort
    
    def __repr__(self):
        """
        Return a string that can be evaluated
        """
        return '{}({})'.format(type(self).__name__, ', '.join(repr(self[feat]) for feat in self.features))
    
    def as_dict(self):
        """
        Return a dict mapping from features to values, including 'cvarsort'
        """
        return dict(self.items())
    
    # Conversion from strings and dicts
    
    @classmethod
    def from_dict(cls, dictionary):
        """
        Instantiates a Sortinfo object from dictionary,
        normalising as necessary
        """
        normalised = cls.normalise_dict(dictionary)
        return cls.from_normalised_dict(normalised)
    
    @staticmethod
    def normalise_dict(dictionary):
        """
        Normalise a sortinfo dictionary - convert keys to lowercase and correct cvarsort if necessary
        """
        # Convert all keys to lowercase (so that we can check if certain keys exist)
        # Values are left untouched until the object is constructed (e.g. in case of None)
        dictionary = {key.lower(): value for key, value in dictionary.items()}
        # Find the cvarsort
        try:
            dictionary['cvarsort'] = dictionary['cvarsort'].lower()
        except KeyError:
            raise PydmrsValueError('Sortinfo must have cvarsort')
        # Correct cvarsort if features are evidence for 'x' or 'e':
        if dictionary['cvarsort'] not in 'ex' and len(dictionary) > 1:
            if any(key in dictionary for key in EventSortinfo.features):  # event evidence
                dictionary['cvarsort'] = 'e'
            elif any(key in dictionary for key in InstanceSortinfo.features):  # instance evidence
                dictionary['cvarsort'] = 'x'
        return dictionary
    
    # In, subclasses, _from_normalised_dict will override from_normalised_dict
    # See SortinfoMeta for details
    @staticmethod
    def from_normalised_dict(dictionary):
        """
        Instantiate a suitable type of Sortinfo from a dictionary,
        mapping from features to values (including cvarsort)
        """
        cvarsort = dictionary['cvarsort']
        # Instantiate an appropriate type of Sortinfo
        if cvarsort == 'e':
            return EventSortinfo.from_normalised_dict(dictionary)
        elif cvarsort == 'x':
            if 'prontype' in dictionary:
                dictionary['pt'] = dictionary.pop('prontype')
            return InstanceSortinfo.from_normalised_dict(dictionary)
        else:
            # This needs to be updated so that the underspecified cvarsorts i, u, and p are distinguished
            return Sortinfo()
    
    @classmethod
    def _from_normalised_dict(cls, dictionary):
        """
        Instantiate from a dictionary mapping features to values
        """
        if 'cvarsort' in dictionary and dictionary['cvarsort'] != cls.cvarsort:
            raise PydmrsValueError('{} must have cvarsort {}, not {}'.format(cls.__name__,
                                                                             cls.cvarsort,
                                                                             dictionary['cvarsort']))
        return cls(**{key:value for key, value in dictionary.items() if key != 'cvarsort'})
    
    @classmethod
    def from_string(cls, string):
        """
        Instantiate from a string of the form:
        cvarsort[feature1=value1, feature2=value2, ...]
        """
        # Force lowercase
        string = string.lower()
        # Dictionary mapping from features to values
        dictionary = {'cvarsort' : string[0]}
        if len(string) > 1:
            if not (string[1] == '[' and string[-1] == ']'):
                raise PydmrsValueError('Sortinfo string must include features in square brackets')
            for item in string[2:-1].split(','):
                key, value = item.split('=')
                dictionary[key.strip()] = value.strip()
        # Convert the dictionary
        return cls.from_dict(dictionary)
    
    # Comparison methods

    def __eq__(self, other):
        """
        Checks two Sortinfos for equality.
        Returns True if all specified features are the same.
        """
        return self.cvarsort == other.cvarsort \
            and set(self.iter_specified()) == set(other.iter_specified())
    
    def __ne__(self, other):
        return not self == other

    def __le__(self, other):
        """
        Checks whether this Sortinfo underspecifies or equals the other Sortinfo.
        Features can be underspecified using '?', or 'u', or None.
        """
        return (self.cvarsort == 'i' or self.cvarsort == other.cvarsort) \
            and all(other[key] == value for key, value in self.iter_specified())
    
    def __lt__(self, other):
        return self <= other and self != other
    
    def __ge__(self, other):
        # Note that "other <= self" will fail with subclasses, due to infinite recursion
        return other.__le__(self)
    
    def __gt__(self, other):
        return self >= other and self != other


class EventSortinfo(Sortinfo):
    """
    Event sortinfo
    """
    cvarsort = 'e'
    __slots__ = ('sf', 'tense', 'mood', 'perf', 'prog')
    # Sentence force, tense, mood, perfect, progressive


class InstanceSortinfo(Sortinfo):
    """
    Instance sortinfo
    """
    cvarsort = 'x'
    __slots__ = ('pers', 'num', 'gend', 'ind', 'pt')
    # Person, number, gender, individuated, pronoun type

