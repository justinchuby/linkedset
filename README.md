# linkedset

An ordered set that is robust against mutation during iteration, implemented in pure Python.

`DoublyLinkedSet` behaves like an ordered set backed by a doubly linked list. Inserting
and removing elements is `O(1)`, and — unlike Python's built-in `list` or `set` — you can
safely add, remove, or move elements *while iterating over the container*.

It implements both `collections.abc.Sequence` (ordered, indexable) and
`collections.abc.MutableSet` (set algebra and in-place updates).

📖 **Documentation**: <https://justinchuby.github.io/linkedset/>

## Installation

```bash
pip install linkedset
```

Or install from source:

```bash
git clone https://github.com/justinchuby/linkedset
cd linkedset
pip install -e ".[dev]"
```

## Usage

```python
from linkedset import DoublyLinkedSet

s = DoublyLinkedSet(["a", "b", "c"])

s.append("d")                 # -> a, b, c, d
s.insert_after("a", ["x"])    # -> a, x, b, c, d
s.insert_before("b", ["y"])   # -> a, x, y, b, c, d
s.remove("c")                 # -> a, x, y, b, d

print(s[0])    # "a"  (O(1))
print(s[-1])   # "d"  (O(1))
print(list(s)) # ['a', 'x', 'y', 'b', 'd']
```

### Safe mutation during iteration

```python
s = DoublyLinkedSet(["a", "b", "c"])
for x in s:
    if x == "a":
        s.insert_after("a", ["d"])  # inserted after current -> iterated
        s.remove("b")               # removed before reached -> skipped
# Iterated: a, d, c
```

Iteration rules:

- Elements inserted **after** the current node **are** iterated over.
- Elements inserted **before** the current node are **not** iterated over in the current pass.
- If the current node is moved to a different location, iteration continues from the node
  that followed it at its *original* location.

### Set operations

Because it is a `MutableSet`, the usual set algebra works and returns a new
`DoublyLinkedSet` (order preserved):

```python
a = DoublyLinkedSet(["a", "b", "c"])
b = DoublyLinkedSet(["c", "d"])

a | b   # union        -> a, b, c, d
a & b   # intersection -> c
a - b   # difference   -> a, b
a ^ b   # symmetric    -> a, b, d

a.add("x")        # idempotent add (no-op if already present)
a.discard("z")    # remove if present, never raises
a.pop()           # remove and return the first element
a |= b            # in-place update

# `==` is order-sensitive, because the set is ordered:
DoublyLinkedSet(["a", "b"]) == DoublyLinkedSet(["a", "b"])  # True
DoublyLinkedSet(["a", "b"]) == DoublyLinkedSet(["b", "a"])  # False
```

## Semantics

- Membership and set operations are based on object **identity** (`id(value)`), not equality.
  Two distinct objects that compare equal are treated as different elements.
- `==` is **order-sensitive** (it is an *ordered* set): equal only when the same elements, by
  identity, appear in the same order. Instances are **not hashable** (mutable set).
- `None` is not a valid value.
- Accessing by index is `O(n)`, except the ends (`s[0]`, `s[-1]`) which are `O(1)`.

## Development

```bash
pip install -e ".[dev]"
python -m pytest      # run tests
python -m ruff check  # lint
```

## License

MIT. Portions derived from the ONNX Project Contributors (Apache-2.0); see `linkedset/__init__.py`.
