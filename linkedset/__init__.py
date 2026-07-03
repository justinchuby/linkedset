# Copyright (c) ONNX Project Contributors
# SPDX-License-Identifier: Apache-2.0
# Modifications Copyright (c) Justin Chu
# SPDX-License-Identifier: MIT
"""Mutable, ordered set with safe mutation properties."""

from __future__ import annotations

from collections.abc import Iterable, Iterator, MutableSet, Sequence
from typing import Generic, TypeVar, overload

__all__ = ["DoublyLinkedSet"]

_T = TypeVar("_T")


class _LinkBox(Generic[_T]):
    """A link in a doubly linked list that has a reference to the actual object in the link.

    The :class:`_LinkBox` is a container for the actual object in the list. It is used to
    maintain the links between the elements in the linked list. The actual object is stored in the
    :attr:`value` attribute.

    By using a separate container for the actual object, we can safely remove the object from the
    list without losing the links. This allows us to remove the object from the list during
    iteration and place the object into a different list without breaking any chains.

    This is an internal class and should only be initialized by the :class:`DoublyLinkedSet`.

    Attributes:
        prev: The previous box in the list.
        next: The next box in the list.
        erased: A flag to indicate if the box has been removed from the list.
        owning_list: The :class:`DoublyLinkedSet` to which the box belongs.
        value: The actual object in the list.
    """

    __slots__ = ("next", "owning_list", "prev", "value")

    def __init__(self, owner: DoublyLinkedSet[_T], value: _T | None) -> None:
        """Create a new link box.

        Args:
            owner: The linked list to which this box belongs.
            value: The value to be stored in the link box. When the value is None,
                the link box is considered erased (default). The root box of the list
                should be created with a None value.
        """
        self.prev: _LinkBox[_T] = self
        self.next: _LinkBox[_T] = self
        self.value: _T | None = value
        self.owning_list: DoublyLinkedSet[_T] = owner

    @property
    def erased(self) -> bool:
        return self.value is None

    def erase(self) -> None:
        """Remove the link from the list and detach the value from the box."""
        if self.value is None:
            raise ValueError("_LinkBox is already erased")
        # Update the links
        prev, next_ = self.prev, self.next
        prev.next, next_.prev = next_, prev
        # Detach the value
        self.value = None

    def __repr__(self) -> str:
        return (
            f"_LinkBox({self.value!r}, erased={self.erased}, "
            f"prev={self.prev.value!r}, next={self.next.value!r})"
        )


class DoublyLinkedSet(Sequence[_T], MutableSet[_T], Generic[_T]):
    """A doubly linked ordered set of nodes.

    The container is both a :class:`collections.abc.Sequence` (ordered, indexable) and a
    :class:`collections.abc.MutableSet`. It does not allow duplicate values and maintains
    insertion order. One can treat it as a doubly linked list with list-like methods, or as
    a mutable set supporting ``&``, ``|``, ``-``, ``^`` and their in-place variants.

    Adding and removing elements from the set during iteration is safe. Moving elements
    from one set to another is also safe.

    During the iteration:

    - If new elements are inserted after the current node, the iterator will
      iterate over them as well.
    - If new elements are inserted before the current node, they will
      not be iterated over in this iteration.
    - If the current node is lifted and inserted in a different location,
      iteration will start from the "next" node at the _original_ location.

    Time complexity:
        Inserting and removing nodes from the set is O(1). Accessing nodes by index is O(n),
        although accessing nodes at either end of the set is O(1). I.e.
        ``linked_set[0]`` and ``linked_set[-1]`` are O(1).

    Membership, uniqueness and set operations are based on value **equality** (``==``),
    not object identity. Two objects that compare equal are treated as the same element,
    and elements must be **hashable** (they are used as keys in an internal ``dict`` that
    gives ``O(1)`` membership and mutation). Because it is a mutable set, instances of
    :class:`DoublyLinkedSet` are themselves not hashable. Since the set is *ordered*, ``==``
    is order-sensitive: two sets are equal only when they hold the same elements (by value)
    in the same order. ``None`` is not a valid value in the set.
    """

    __slots__ = ("_length", "_root", "_value_to_boxes")

    def __init__(self, values: Iterable[_T] | None = None) -> None:
        # Using the root node simplifies the mutation implementation a lot
        # The list is circular. The root node is the only node that is not a part of the list values
        root_ = _LinkBox(self, None)
        self._root: _LinkBox = root_
        self._length = 0
        self._value_to_boxes: dict[_T, _LinkBox] = {}
        if values is not None:
            self.extend(values)

    def __iter__(self) -> Iterator[_T]:
        """Iterate over the elements in the list.

        - If new elements are inserted after the current node, the iterator will
          iterate over them as well.
        - If new elements are inserted before the current node, they will
          not be iterated over in this iteration.
        - If the current node is lifted and inserted in a different location,
          iteration will start from the "next" node at the _original_ location.
        """
        box = self._root.next
        while box is not self._root:
            if box.owning_list is not self:
                raise RuntimeError(f"Element {box!r} is not in the list")
            if not box.erased:
                assert box.value is not None
                yield box.value
            box = box.next

    def __reversed__(self) -> Iterator[_T]:
        """Iterate over the elements in the list in reverse order."""
        box = self._root.prev
        while box is not self._root:
            if not box.erased:
                assert box.value is not None
                yield box.value
            box = box.prev

    def __len__(self) -> int:
        assert self._length == len(self._value_to_boxes), (
            "Bug in the implementation: length mismatch"
        )
        return self._length

    def _find_box_for_equal_value(self, value: object) -> _LinkBox[_T] | None:
        """Find and return the box containing a value equal to the given value.

        This uses the dictionary for O(1) lookup. Values must be hashable.
        """
        return self._value_to_boxes.get(value)

    def __contains__(self, value: object) -> bool:
        """Return whether ``value`` is in the set using value equality (O(1))."""
        return value in self._value_to_boxes

    def __eq__(self, other: object) -> bool:
        """Return whether ``other`` is an equal, equally-ordered set.

        Because :class:`DoublyLinkedSet` is *ordered*, equality is order-sensitive
        (unlike a plain :class:`set`). Two sets are equal only when they contain the same
        elements by value equality, in the same order. Only another
        :class:`DoublyLinkedSet` can compare equal.
        """
        if self is other:
            return True
        if not isinstance(other, DoublyLinkedSet):
            return NotImplemented
        if self._length != other._length:
            return False
        return all(a == b for a, b in zip(self, other))

    __hash__ = None  # type: ignore[assignment]  # ordered, mutable -> unhashable

    def count(self, value: object) -> int:
        """Return the number of occurrences of ``value`` (0 or 1) using value equality (O(1))."""
        return 1 if value in self._value_to_boxes else 0

    def index(self, value: object, start: int = 0, stop: int | None = None) -> int:
        """Return the index of ``value`` in the set using value equality.

        Raises:
            ValueError: If ``value`` is not present in ``self[start:stop]``.
        """
        length = self._length
        if start < 0:
            start = max(length + start, 0)
        if stop is None:
            stop = length
        elif stop < 0:
            stop += length
        for i, item in enumerate(self):
            if i >= stop:
                break
            if i >= start and item == value:
                return i
        raise ValueError(f"{value!r} is not in the set")

    @overload
    def __getitem__(self, index: int) -> _T: ...
    @overload
    def __getitem__(self, index: slice) -> Sequence[_T]: ...

    def __getitem__(self, index):
        """Get the node at the given index.

        Complexity is O(n).
        """
        if isinstance(index, slice):
            return tuple(self)[index]
        if index >= self._length or index < -self._length:
            raise IndexError(
                f"Index out of range: {index} not in range [-{self._length}, {self._length})"
            )
        if index < 0:
            # Look up from the end of the list
            iterator = reversed(self)
            item = next(iterator)
            for _ in range(-index - 1):
                item = next(iterator)
        else:
            iterator = iter(self)  # type: ignore[assignment]
            item = next(iterator)
            for _ in range(index):
                item = next(iterator)
        return item

    def _insert_one_after(
        self,
        box: _LinkBox[_T],
        new_value: _T,
    ) -> _LinkBox[_T]:
        """Insert a new value after the given box.

        All insertion methods should call this method to ensure that the list is updated correctly.

        Example::
            Before: A  <->  B  <->  C
                    ^v0     ^v1     ^v2
            Call: _insert_one_after(B, v3)
            After:  A  <->  B  <->  new_box  <->  C
                    ^v0     ^v1       ^v3         ^v2

        Args:
            box: The box which the new value is to be inserted.
            new_value: The new value to be inserted.
        """
        if new_value is None:
            raise TypeError(f"{self.__class__.__name__} does not support None values")
        if box.value == new_value:
            # Do nothing if the new value is equal to the old value
            return box
        if box.owning_list is not self:
            raise ValueError(f"Value {box.value!r} is not in the list")

        # Check if an equal value is already in the list
        existing_box = self._find_box_for_equal_value(new_value)
        if existing_box is not None:
            # If an equal value is already in the list, remove it first
            self.remove(new_value)

        # Create a new _LinkBox for the new value
        new_box = _LinkBox(self, new_value)
        # original_box <=> original_next
        # becomes
        # original_box <=> new_box <=> original_next
        original_next = box.next
        box.next = new_box
        new_box.prev = box
        new_box.next = original_next
        original_next.prev = new_box

        # Be sure to update the length and mapping
        self._length += 1
        self._value_to_boxes[new_value] = new_box

        return new_box

    def _insert_many_after(
        self,
        box: _LinkBox[_T],
        new_values: Iterable[_T],
    ):
        """Insert multiple new values after the given box."""
        insertion_point = box
        for new_value in new_values:
            insertion_point = self._insert_one_after(insertion_point, new_value)

    def remove(self, value: _T) -> None:
        """Remove a node from the list."""
        box = self._value_to_boxes.get(value)
        if box is None:
            raise ValueError(f"Value {value!r} is not in the list")
        # Remove the link box and detach the value from the box
        box.erase()

        # Be sure to update the length and mapping
        self._length -= 1
        del self._value_to_boxes[value]

    def add(self, value: _T) -> None:
        """Add ``value`` to the end of the set if it is not already present.

        Unlike :meth:`append`, this is idempotent: if ``value`` (by equality) is already
        in the set, its position is left unchanged. This implements
        :meth:`collections.abc.MutableSet.add`.
        """
        if value not in self._value_to_boxes:
            self.append(value)

    def discard(self, value: _T) -> None:
        """Remove ``value`` from the set if it is present, without raising otherwise.

        This implements :meth:`collections.abc.MutableSet.discard`.
        """
        if value in self._value_to_boxes:
            self.remove(value)

    def append(self, value: _T) -> None:
        """Append a node to the list."""
        _ = self._insert_one_after(self._root.prev, value)

    def extend(
        self,
        values: Iterable[_T],
    ) -> None:
        for value in values:
            self.append(value)

    def appendleft(self, value: _T) -> None:
        """Add ``value`` to the front of the set (deque-style).

        If ``value`` is already present (by equality), it is moved to the front.
        """
        _ = self._insert_one_after(self._root, value)

    def extendleft(self, values: Iterable[_T]) -> None:
        """Prepend each value in ``values`` to the front of the set (deque-style).

        As with :meth:`collections.deque.extendleft`, the prepended items end up in reverse
        order relative to ``values``.
        """
        for value in values:
            self.appendleft(value)

    def _box_at(self, index: int) -> _LinkBox[_T]:
        """Return the live link box at ``index`` in ``[0, len)``, walking from the nearer end."""
        if index <= self._length - 1 - index:
            box = self._root.next
            for _ in range(index):
                box = box.next
        else:
            box = self._root.prev
            for _ in range(self._length - 1 - index):
                box = box.prev
        return box

    def insert(self, index: int, value: _T) -> None:
        """Insert ``value`` before position ``index`` (list/deque-style).

        ``index`` is clamped like :meth:`list.insert`. If ``value`` is already present it is
        removed first, so ``index`` refers to a position in the resulting sequence.
        """
        if value is None:
            raise TypeError(f"{self.__class__.__name__} does not support None values")
        if value in self._value_to_boxes:
            self.remove(value)
        length = self._length
        if index < 0:
            index = max(length + index, 0)
        if index >= length:
            self.append(value)
            return
        target = self._box_at(index)
        self._insert_one_after(target.prev, value)

    def pop(self, index: int = -1) -> _T:
        """Remove and return the value at ``index`` (default: the last one, list-style).

        Raises:
            IndexError: If the set is empty or ``index`` is out of range.
        """
        if self._length == 0:
            raise IndexError("pop from empty DoublyLinkedSet")
        value = self[index]
        self.remove(value)
        return value

    def popleft(self) -> _T:
        """Remove and return the first value (deque-style).

        Raises:
            IndexError: If the set is empty.
        """
        if self._length == 0:
            raise IndexError("popleft from empty DoublyLinkedSet")
        value = self[0]
        self.remove(value)
        return value

    def clear(self) -> None:
        """Remove all elements from the set.

        Safe to call during iteration: existing nodes are marked erased (so a live iterator
        stops yielding them) before the set is reset.
        """
        box = self._root.next
        while box is not self._root:
            # Detach the value but keep next/prev intact so a live iterator can still advance.
            nxt = box.next
            box.value = None
            box = nxt
        self._root.prev = self._root
        self._root.next = self._root
        self._length = 0
        self._value_to_boxes.clear()

    def reverse(self) -> None:
        """Reverse the elements of the set in place.

        Note:
            Unlike per-element mutation, this is a global reorder and is **not** safe to call
            while iterating over the set: an in-progress iterator may then skip or repeat
            elements.
        """
        node = self._root.next
        while node is not self._root:
            nxt = node.next
            node.next, node.prev = node.prev, node.next
            node = nxt
        self._root.next, self._root.prev = self._root.prev, self._root.next

    def rotate(self, n: int = 1) -> None:
        """Rotate the set ``n`` steps to the right (deque-style).

        Negative ``n`` rotates to the left. ``rotate(1)`` moves the last element to the front.

        Note:
            Like :meth:`reverse`, this is a global reorder and is **not** safe to call while
            iterating over the set.
        """
        length = self._length
        if length <= 1:
            return
        n %= length
        if n == 0:
            return
        # The new first element is the n-th element counted from the end.
        new_head = self._root.prev
        for _ in range(n - 1):
            new_head = new_head.prev
        new_tail = new_head.prev
        old_head = self._root.next
        old_tail = self._root.prev
        # Close the value ring, removing the root sentinel from between old_tail and old_head.
        old_tail.next = old_head
        old_head.prev = old_tail
        # Splice the root sentinel back in between new_tail and new_head.
        new_tail.next = self._root
        self._root.prev = new_tail
        self._root.next = new_head
        new_head.prev = self._root

    def copy(self) -> DoublyLinkedSet[_T]:
        """Return a shallow copy of the set, preserving order."""
        return DoublyLinkedSet(self)

    # -- Set algebra -------------------------------------------------------------------------
    # These override the collections.abc.Set mixins to use value equality semantics
    # and preserve this set's (left-operand) order.

    def __and__(self, other: Iterable[_T]) -> DoublyLinkedSet[_T]:
        if not isinstance(other, Iterable):
            return NotImplemented
        other_set = set(other)
        result: DoublyLinkedSet[_T] = DoublyLinkedSet()
        for value in self:
            if value in other_set:
                result.append(value)
        return result

    def __rand__(self, other: Iterable[_T]) -> DoublyLinkedSet[_T]:
        # Reflected: ``other`` is the left operand, so honour its order.
        if not isinstance(other, Iterable):
            return NotImplemented
        result: DoublyLinkedSet[_T] = DoublyLinkedSet()
        for value in other:
            if value in self._value_to_boxes:
                result.append(value)
        return result

    def __or__(self, other: Iterable[_T]) -> DoublyLinkedSet[_T]:
        if not isinstance(other, Iterable):
            return NotImplemented
        result = self.copy()
        for value in other:
            result.add(value)
        return result

    def __ror__(self, other: Iterable[_T]) -> DoublyLinkedSet[_T]:
        if not isinstance(other, Iterable):
            return NotImplemented
        result: DoublyLinkedSet[_T] = DoublyLinkedSet(other)
        for value in self:
            result.add(value)
        return result

    def __sub__(self, other: Iterable[_T]) -> DoublyLinkedSet[_T]:
        if not isinstance(other, Iterable):
            return NotImplemented
        other_set = set(other)
        result: DoublyLinkedSet[_T] = DoublyLinkedSet()
        for value in self:
            if value not in other_set:
                result.append(value)
        return result

    def __rsub__(self, other: Iterable[_T]) -> DoublyLinkedSet[_T]:
        if not isinstance(other, Iterable):
            return NotImplemented
        result: DoublyLinkedSet[_T] = DoublyLinkedSet()
        for value in other:
            if value not in self._value_to_boxes:
                result.append(value)
        return result

    def __xor__(self, other: Iterable[_T]) -> DoublyLinkedSet[_T]:
        if not isinstance(other, Iterable):
            return NotImplemented
        other_list = list(other)
        other_set = set(other_list)
        result: DoublyLinkedSet[_T] = DoublyLinkedSet()
        # Add values from self that are not in other
        for value in self:
            if value not in other_set:
                result.append(value)
        # Add values from other that are not in self
        for other_value in other_list:
            if other_value not in self._value_to_boxes:
                result.append(other_value)
        return result

    def __rxor__(self, other: Iterable[_T]) -> DoublyLinkedSet[_T]:
        # Reflected: ``other`` is the left operand, so emit its unique values first, in order.
        if not isinstance(other, Iterable):
            return NotImplemented
        other_list = list(other)
        other_set = set(other_list)
        result: DoublyLinkedSet[_T] = DoublyLinkedSet()
        for value in other_list:
            if value not in self._value_to_boxes:
                result.append(value)
        for value in self:
            if value not in other_set:
                result.append(value)
        return result

    def isdisjoint(self, other: Iterable[_T]) -> bool:
        """Return ``True`` if the set has no elements (by equality) in common with ``other``."""
        return not any(value in self._value_to_boxes for value in other)

    def _unsupported_ordering(self, _other: object) -> bool:
        raise TypeError(
            f"{type(self).__name__} does not support ordering/subset comparisons "
            "(<, <=, >, >=) because '==' is order-sensitive; "
            "use set algebra (&, |, -, ^) or isdisjoint() instead"
        )

    # Subset/superset ordering would clash with the order-sensitive ``==``, so it is disabled.
    __lt__ = __le__ = __gt__ = __ge__ = _unsupported_ordering

    def insert_after(
        self,
        value: _T,
        new_values: Iterable[_T],
    ) -> None:
        """Insert new nodes after the given node.

        Args:
            value: The value after which the new values are to be inserted.
            new_values: The new values to be inserted.
        """
        insertion_point = self._find_box_for_equal_value(value)
        if insertion_point is None:
            raise ValueError(f"Value {value!r} is not in the list")
        return self._insert_many_after(insertion_point, new_values)

    def insert_before(
        self,
        value: _T,
        new_values: Iterable[_T],
    ) -> None:
        """Insert new nodes before the given node.

        Args:
            value: The value before which the new values are to be inserted.
            new_values: The new values to be inserted.
        """
        insertion_point_box = self._find_box_for_equal_value(value)
        if insertion_point_box is None:
            raise ValueError(f"Value {value!r} is not in the list")
        return self._insert_many_after(insertion_point_box.prev, new_values)

    def __repr__(self) -> str:
        return f"DoublyLinkedSet({list(self)})"
