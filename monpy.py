from typing import Callable, Any
from threading import Thread


def _curry_call(f, x, n, xs=()):
    if n == 1:
        return f(x, *xs)
    else:
        return lambda x_: _curry_call(f, x_, n - 1, (*xs, x))


def curry(n): return lambda f: lambda x: _curry_call(f, x, n)


def _un_curry_call(f, xs, n):
    if len(xs) != n: raise Exception(f"function takes {n} positional arguments but {len(xs)} were given")
    y = f
    for x in xs:
        y = f(x)
    return y


def un_curry(n): return lambda f: lambda *xs: _un_curry_call(f, xs, n)


def flatten(mon, expr):
    """Simplifies nested monads using type checking.
    """
    return mon.loop(
        lambda s: issubclass(type(s.x), mon),
        do = mon.do(x = lambda s: expr),
        x = lambda s: s.x
    ).map(lambda s: s.x)


def functor(cls: type):
    """Adds Functor methods to a class.

    Replaces cls with FunctorCls(cls):
    - expects obj.map
    - provides cls.mmap
    """
    class FunctorCls(cls):
        def __init__(self,  *args, **kwargs):
            cls.__init__(self, *args, **kwargs)

        @classmethod
        def mmap(cls, *functor_levels: int):
            """Refactors a function to map through successive layers of a functor.

            For example: fffw = cls.mmap(1, 2, 0)(f)(fx, ffy, z).
            """
            flevs_len = len(functor_levels)
            if flevs_len <= 0: raise Exception("Can only multi-map a strictly positive number of positional arguments")

            def inner(f, args):
                if len(args) != flevs_len: raise Exception(f"function takes {flevs_len} positional arguments but {len(args)} were given")
                layer = 0
                y = curry(flevs_len)(f)
                for i in range(flevs_len):
                    update = lambda y_, x: y_(x)
                    for _ in [None] * functor_levels[i]:
                        u = update
                        update = lambda y_, x, u=u: x.map(lambda x_, u=u: u(y_, x_))
                    for _ in [None] * layer:
                        u = update
                        update = lambda y_, x, u=u: y_.map(lambda y__, u=u: u(y__, x))
                    layer += functor_levels[i]
                    y = update(y, args[i])
                return y

            return lambda f: lambda *args: inner(f, args)

    return type(cls.__name__, (FunctorCls,), dict())


def applicative(cls: type):
    """Adds Applicative methods to a class.

    Replaces cls with ApplicativeCls(cls):
    - expects cls.wrap
    - expects obj.apply
    - provides cls.lift
    """
    class ApplicativeCls(cls):
        def __init__(self,  *args, **kwargs):
            cls.__init__(self, *args, **kwargs)

        @classmethod
        def lift(cls, *applicative_flags: bool):
            """Refactors a function to map through successive layers of a functor.

            For example: fw = cls.lift(true, false, true)(f)(fx, y, fz).
            """
            aflags_len = len(applicative_flags)
            if aflags_len <= 0: raise Exception("Can only lift a strictly positive number of positional arguments")

            def inner(f, args):
                if len(args) != aflags_len: raise Exception(f"function takes {aflags_len} positional arguments but {len(args)} were given")
                y = cls.wrap(curry(aflags_len)(f))
                for i in range(aflags_len):
                    if applicative_flags[i]:
                        y = y.apply(args[i])
                    else:
                        y = y.map(lambda f_: f_(args[i]))
                return y

            return lambda f: lambda *args: inner(f, args)

    return type(cls.__name__, (ApplicativeCls,), dict())


class Do(object):
    """Represents the state of a procedure.

    Used in the creation of do blocks as a monadic state.
    """
    def __init__(self, **state):
        self.state = state

    def __getattribute__(self, name):
        if name == "do":
            return object.__getattribute__(self, "state")
        elif name in {'__init__', '__getattribute__'}:
            return object.__getattribute__(self, name)
        else:
            return object.__getattribute__(self, "state")[name]


def monad(cls: type):
    """Adds Monadic methods to a class.

    Replaces cls with MonadCls(cls):
    - expects obj.bind
    - provides cls.do
    - provides cls.loop
    """
    class MonadCls(cls):
        def __init__(self,  *args, **kwargs):
            cls.__init__(self, *args, **kwargs)

        @classmethod
        def do(cls, do: Any = None, **kwargs: Callable[[Do], Any]):
            """Constructs a do block (like in Haskell) using an ordered dictionary of lambdas from state to wrapped value.

            Due to the fact that dictionaries and kwargs are ordered in python, kwargs can be used to define procedural blocks;
            this allows for monad procedures, or "do blocks", where instead of mapping from previous state to new state each line
            instead maps from previous state to new state wrapped in some monad. By using `.bind` a procedure can be formed nonetheless.

            For example: mstate = cls.do(do=cls.wrap(**kwargs), x=lambda state: ..., y=lambda state: ...).
            """
            if do == None: do = cls.wrap(Do())
            state = do
            for name, line in kwargs.items():
                state = state.bind(lambda s, line=line, name=name: line(s).map(lambda x, name=name: Do(**{**s.do, name: x})))
            return state

        @classmethod
        def loop(cls, predicate: Callable[[Do], bool], do: Any = None, **kwargs: Callable[[Do], Any]):
            """Constructs a recursive do block using an ordered dictionary of lambdas from state to wrapped value that only runs whilst the predicate is true.

            For example: mstate = cls.loop(lambda state: state.y..., do=cls.wrap(y=...), x=lambda state: ..., y=lambda state: ...).
            """
            if do == None: do = cls.wrap(Do())
            def while_do(s):
                if predicate(s):
                    return cls.do(do=cls.wrap(s), **kwargs).bind(while_do)
                else:
                    return cls.wrap(s)
            return do.bind(while_do)

    return type(cls.__name__, (MonadCls,), dict())


# Box Monad: is simple wrapper
@monad
@applicative
@functor
class Box:
    def __init__(self, obj):
        self.obj = obj

    def __repr__(self):
        return f"Box{repr(self.obj)}"

    def __str__(self):
        return str(self.obj)

    def unwrap(self) -> Any:
        return self.obj

    # apply to wrapped state
    def map(self, f: Callable[[Any], Any]) -> 'Box':
        return Box(f(self.obj))

    # wrap value
    @classmethod
    def wrap(cls, x: Any) -> 'Box':
        return Box(x)

    # apply inner function
    def apply(self, other: 'Box') -> 'Box':
        return Box(self.obj(other.obj))

    # combine side effects
    def bind(self, f: Callable[[Any], 'Box']) -> 'Box':
        return f(self.obj)


# Maybe Monad: may contain value
@monad
@applicative
@functor
class Maybe:
    def __init__(self, *args):
        match args:
            case []:
                self.val = ()
            case [x]:
                self.val = (x,)
            case _:
                raise Exception(f"Maybe takes 0 or 1 arguments, {len(args)} were given")

    def __repr__(self):
        match self.val:
            case ():
                return "Maybe()"
            case (x,):
                return f"Maybe({repr(x)})"

    def __str__(self):
        match self.val:
            case ():
                return "Nothing"
            case (x,):
                return str(x)

    # provide default value
    def otherwise(self, alt: Any) -> Any:
        match self.val:
            case ():
                return alt
            case (x,):
                return x

    # apply to wrapped state
    def map(self, f: Callable[[Any], Any]) -> 'Maybe':
        match self.val:
            case ():
                return Maybe()
            case (x,):
                return Maybe(f(x))

    # wrap value
    @classmethod
    def wrap(cls, x: Any) -> 'Maybe':
        return Maybe(x)

    # apply inner function
    def apply(self, other: 'Maybe') -> 'Maybe':
        match self.val:
            case ():
                return Maybe()
            case (f,):
                match other.val:
                    case ():
                        return Maybe()
                    case (x,):
                        return Maybe(f(x))

    # combine side effects
    def bind(self, f: Callable[[Any], 'Maybe']) -> 'Maybe':
        match self.val:
            case ():
                return Maybe()
            case (x,):
                return f(x)


# Many Monad: contains many values
@monad
@applicative
@functor
class Many:
    def __init__(self, *args):
        self.tup = tuple(args)

    def __repr__(self):
        return f"Many{repr(self.tup)}"

    def __str__(self):
        return str(self.tup)

    def __len__(self):
        return len(self.tup)

    def __iter__(self):
        return iter(self.tup)

    def __getitem__(self, item):
        return self.tup[item]

    def __contains__(self, item):
        return item in self.tup

    def filter(self, pred: Callable[[Any], bool]) -> 'Many':
        return Many(*[x for x in self.tup if pred(x)])

    def fold(self, initial: Any, fold: Callable[[Any, Any], Any]) -> Any:
        y = initial
        for x in self.tup:
            y = fold(y, x)
        return y

    # apply to wrapped state
    def map(self, f: Callable[[Any], Any]) -> 'Many':
        return Many(*map(f, self.tup))

    # wrap value
    @classmethod
    def wrap(cls, x: Any) -> 'Many':
        return Many(x)

    # apply inner function
    def apply(self, other: 'Many') -> 'Many':
        return Many(*(f(x) for f in self.tup for x in other.tup))

    # combine side effects
    def bind(self, f: Callable[[Any], 'Many']) -> 'Many':
        return Many(*(x for mx in map(f, self.tup) for x in mx.tup))


# Func Monad: is a function
@monad
@applicative
@functor
class Func:
    def __init__(self, func):
        self.func = func

    def __call__(self, arg):
        return self.func(arg)

    def __repr__(self):
        return f"Func{repr(self.func)}"

    def __str__(self):
        return "arrow-function"

    # apply to wrapped state
    def map(self, f: Callable[[Any], Any]) -> 'Func':
        return Func(lambda arg: f(self(arg)))

    # wrap value
    @classmethod
    def wrap(cls, x: Any) -> 'Func':
        return Func(lambda arg: x)

    # apply inner function
    def apply(self, other: 'Func') -> 'Func':
        return Func(lambda arg: self(arg)(other(arg)))

    # combine side effects
    def bind(self, f: Callable[[Any], 'Func']) -> 'Func':
        return Func(lambda arg: f(self(arg))(arg))


# Async Monad: represents a thread
@monad
@applicative
@functor
class Async:
    def __init__(self, proc):
        self.result = None
        def cb(res): self.result = res
        self.thread = Thread(target=lambda cb=cb: cb(proc()), args=())
        self.thread.start()

    def join(self, timeout=None):
        self.thread.join(timeout=timeout)
        return self.result

    # apply to wrapped state
    def map(self, f: Callable[[Any], Any]) -> 'Async':
        return Async(lambda: f(self.join()))

    # wrap value
    @classmethod
    def wrap(cls, x: Any) -> 'Async':
        return Async(lambda: x)

    # apply inner function
    def apply(self, other: 'Async') -> 'Async':
        return Async(lambda: self.join()(other.join()))

    # combine side effects
    def bind(self, f: Callable[[Any], 'Async']) -> 'Async':
        return Async(lambda: f(self.join()).join())