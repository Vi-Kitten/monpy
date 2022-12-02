# monpy
Monad decorators mini-lib for python.

Bringing simple functional programming to python.

## example
In this example a `do` block is used to remove the need for nested `if` statements.
```py
Maybe.do(
    x = lambda s: may_fail(...),
    y = lambda s: Maybe.wrap(wont_fail(s.x)),
    z = lambda s: may_also_fail(s.x, s.y)
).map(lambda s: s.z) # return z
```

## decorations
Each decorator in order expects that the previous one has been applied and that all the qualifications are met:

### functor
`@functor`:
- **expects** `obj.map` Impliments functor map funcitonality.
- **provides** `cls.mmap` Refactors a function to map through successive layers of a functor.

### applicative
`@applicative`:
- **expects** `cls.wrap` Trivially constructs a "singleton" instance.
- **expects** `obj.apply` Combines a wrapped function to a wrapped value to produce a wrapped result.
- **provides** `cls.lift` Refactors a function to map through successive layers of a functor.

### monad
`@monad`:
- **expects** `obj.bind` Generalisation of flatmap.
- **provides** `cls.do` Constructs a do block (like in Haskell) using an ordered dictionary of lambdas from state to wrapped value.
- **provides** `cls.loop` Constructs a recursive do block using an ordered dictionary of lambdas from state to wrapped value that only runs whilst the predicate is true.

## types
The library comes with a handful of monad types:
- `Box` for simple wrapping.
- `Maybe` for optional values.
- `Many` for multiple values.
- `Func` for lambdas.
- `Async` for asyncronous lambdas.

## helpers
The library also includes some helper functions:
- `curry` Seperates positional arguments into seperate calls.
- `un_curry` Inverts `curry`.
- `flatten` Simplifies nested monads using type checking.


## about "Do"
The `Do` type exists to represent the state of a procedure as a wrapped dictionaty with an overloaded `__getattribute__` method to make `do` syntax clean.

`.do` will retrieve the dictionary itself.
