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

## Complexity

`DoublyLinkedSet` is a doubly linked list paired with a `dict` mapping each element's
`id()` to its list node. That combination gives set-like `O(1)` membership and endpoint
mutation, while preserving order and safe mutation during iteration.

Let `n` be the size of the set (and `m` the size of the other operand for binary set
operations).

| Operation | Complexity | Notes |
| --- | --- | --- |
| `x in s`, `s.count(x)` | `O(1)` | `dict` lookup by `id(x)` |
| `len(s)` | `O(1)` | length is tracked, not counted |
| `s.append(x)`, `s.add(x)` | `O(1)` | insert at the tail |
| `s.remove(x)`, `s.discard(x)` | `O(1)` | unlink the node, no shifting |
| `s.insert_after(v, xs)`, `s.insert_before(v, xs)` | `O(k)` | `k = len(xs)`; `O(1)` per element |
| `s.pop()` | `O(1)` | removes and returns the first element |
| `s[0]`, `s[-1]` | `O(1)` | endpoints are reachable directly |
| `s[i]` | `O(\|i\|)` | walks from the nearer end |
| `s.index(x)` | `O(n)` | linear scan for position |
| `s.clear()` | `O(n)` | |
| iteration, `reversed(s)`, `s == other` | `O(n)` | |
| `s[a:b]` (slice) | `O(n)` | materialises a tuple |
| `s \| t`, `s & t`, `s - t`, `s ^ t` | `O(n + m)` | each membership test is `O(1)` |
| `s <= t`, `s < t`, `s.isdisjoint(t)` | `O(n)` | one pass with `O(1)` lookups |

Space is `O(n)`: every element is wrapped in a small link node and referenced once from the
`id`-keyed index.

Mutating during iteration stays `O(1)` per operation. Removed nodes are unlinked from their
neighbours immediately, so a traversal never pays to skip over dead nodes — the only cost is
following the `next` pointer you already hold.

## Development

```bash
pip install -e ".[dev]"
python -m pytest      # run tests
python -m ruff check  # lint
```

## License

MIT. Portions derived from the ONNX Project Contributors (Apache-2.0); see `linkedset/__init__.py`.
