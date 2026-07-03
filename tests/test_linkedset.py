# Copyright (c) Justin Chu
# SPDX-License-Identifier: MIT
"""Tests for :class:`linkedset.DoublyLinkedSet`."""

from __future__ import annotations

from collections.abc import MutableSet, Sequence, Set

import pytest

from linkedset import DoublyLinkedSet


def test_empty_set():
    s: DoublyLinkedSet[str] = DoublyLinkedSet()
    assert len(s) == 0
    assert list(s) == []
    assert repr(s) == "DoublyLinkedSet([])"


def test_init_from_iterable():
    s = DoublyLinkedSet(["a", "b", "c"])
    assert list(s) == ["a", "b", "c"]
    assert len(s) == 3


def test_append_and_extend():
    s: DoublyLinkedSet[str] = DoublyLinkedSet()
    s.append("a")
    s.extend(["b", "c"])
    assert list(s) == ["a", "b", "c"]


def test_repr():
    s = DoublyLinkedSet(["a", "b"])
    assert repr(s) == "DoublyLinkedSet(['a', 'b'])"


def test_reversed():
    s = DoublyLinkedSet(["a", "b", "c"])
    assert list(reversed(s)) == ["c", "b", "a"]


def test_indexing_positive():
    s = DoublyLinkedSet(["a", "b", "c"])
    assert s[0] == "a"
    assert s[1] == "b"
    assert s[2] == "c"


def test_indexing_negative():
    s = DoublyLinkedSet(["a", "b", "c"])
    assert s[-1] == "c"
    assert s[-2] == "b"
    assert s[-3] == "a"


def test_indexing_out_of_range():
    s = DoublyLinkedSet(["a", "b", "c"])
    with pytest.raises(IndexError):
        _ = s[3]
    with pytest.raises(IndexError):
        _ = s[-4]


def test_slice():
    s = DoublyLinkedSet(["a", "b", "c", "d"])
    assert s[1:3] == ("b", "c")
    assert s[::-1] == ("d", "c", "b", "a")


def test_remove():
    s = DoublyLinkedSet(["a", "b", "c"])
    s.remove("b")
    assert list(s) == ["a", "c"]
    assert len(s) == 2


def test_remove_missing_raises():
    s = DoublyLinkedSet(["a"])
    with pytest.raises(ValueError):
        s.remove("z")


def test_none_value_rejected():
    s: DoublyLinkedSet = DoublyLinkedSet()
    with pytest.raises(TypeError):
        s.append(None)  # type: ignore[arg-type]


def test_insert_after():
    s = DoublyLinkedSet(["a", "b", "c"])
    s.insert_after("a", ["x", "y"])
    assert list(s) == ["a", "x", "y", "b", "c"]


def test_insert_before():
    s = DoublyLinkedSet(["a", "b", "c"])
    s.insert_before("b", ["x", "y"])
    assert list(s) == ["a", "x", "y", "b", "c"]


def test_insert_after_missing_raises():
    s = DoublyLinkedSet(["a"])
    with pytest.raises(ValueError):
        s.insert_after("z", ["x"])


def test_insert_before_missing_raises():
    s = DoublyLinkedSet(["a"])
    with pytest.raises(ValueError):
        s.insert_before("z", ["x"])


def test_duplicate_insertion_moves_element():
    # Re-inserting an existing value moves it to the new location.
    s = DoublyLinkedSet(["a", "b", "c"])
    s.insert_after("a", ["c"])
    assert list(s) == ["a", "c", "b"]
    assert len(s) == 3


def test_no_op_when_reinserting_same_position():
    s = DoublyLinkedSet(["a", "b"])
    # Inserting "b" right after "a" where it already is.
    s.insert_after("a", ["b"])
    assert list(s) == ["a", "b"]


class TestIterationSafeMutation:
    def test_insert_after_current_is_iterated(self):
        s = DoublyLinkedSet(["a", "b", "c"])
        seen = []
        for x in s:
            seen.append(x)
            if x == "a":
                s.insert_after("a", ["d"])
        assert seen == ["a", "d", "b", "c"]

    def test_insert_before_current_is_not_iterated(self):
        s = DoublyLinkedSet(["a", "b", "c"])
        seen = []
        for x in s:
            seen.append(x)
            if x == "b":
                s.insert_before("b", ["d"])
        assert seen == ["a", "b", "c"]
        assert list(s) == ["a", "d", "b", "c"]

    def test_remove_current_during_iteration(self):
        s = DoublyLinkedSet(["a", "b", "c"])
        seen = []
        for x in s:
            seen.append(x)
            if x == "b":
                s.remove("b")
        assert seen == ["a", "b", "c"]
        assert list(s) == ["a", "c"]

    def test_remove_upcoming_during_iteration(self):
        s = DoublyLinkedSet(["a", "b", "c"])
        seen = []
        for x in s:
            seen.append(x)
            if x == "a":
                s.remove("b")
        assert seen == ["a", "c"]

    def test_move_current_continues_from_original_next(self):
        s = DoublyLinkedSet(["a", "b", "c"])
        seen = []
        for x in s:
            seen.append(x)
            if x == "a":
                # Lift "a" and move it after "c".
                s.insert_after("c", ["a"])
        # Iteration continues from the node after the original location of "a";
        # because "a" now lives at the end, it is visited again there.
        assert seen == ["a", "b", "c", "a"]
        assert list(s) == ["b", "c", "a"]


def test_len_matches_iteration():
    s = DoublyLinkedSet(range(10))
    assert len(s) == len(list(s)) == 10


def test_identity_semantics():
    # The set uses object identity, not equality.
    a = int("1000")
    b = int("1000")  # distinct object with an equal value
    assert a is not b
    s = DoublyLinkedSet([a])
    s.append(b)
    # Both distinct objects are stored.
    assert len(s) == 2


class TestSetInterface:
    def test_is_sequence_and_mutableset(self):
        s = DoublyLinkedSet(["a"])
        assert isinstance(s, Sequence)
        assert isinstance(s, MutableSet)
        assert isinstance(s, Set)

    def test_contains_uses_identity(self):
        a = int("1000")
        b = int("1000")
        s = DoublyLinkedSet([a])
        assert a in s
        assert b not in s  # equal value, different identity
        assert "z" not in s

    def test_add_is_idempotent(self):
        s = DoublyLinkedSet(["a", "b"])
        s.add("a")  # already present -> no move, no duplicate
        assert list(s) == ["a", "b"]
        s.add("c")
        assert list(s) == ["a", "b", "c"]

    def test_discard_missing_is_silent(self):
        s = DoublyLinkedSet(["a"])
        s.discard("z")  # no error
        assert list(s) == ["a"]
        s.discard("a")
        assert list(s) == []

    def test_pop(self):
        s = DoublyLinkedSet(["a", "b", "c"])
        assert s.pop() == "a"
        assert list(s) == ["b", "c"]

    def test_pop_empty_raises(self):
        s: DoublyLinkedSet[str] = DoublyLinkedSet()
        with pytest.raises(KeyError):
            s.pop()

    def test_clear(self):
        s = DoublyLinkedSet(["a", "b", "c"])
        s.clear()
        assert list(s) == []
        assert len(s) == 0

    def test_union(self):
        a, b, c, d = "a", "b", "c", "d"
        result = DoublyLinkedSet([a, b, c]) | DoublyLinkedSet([c, d])
        assert isinstance(result, DoublyLinkedSet)
        assert list(result) == [a, b, c, d]

    def test_intersection(self):
        a, b, c, d = "a", "b", "c", "d"
        assert list(DoublyLinkedSet([a, b, c]) & DoublyLinkedSet([b, c, d])) == [b, c]

    def test_difference(self):
        a, b, c, d = "a", "b", "c", "d"
        assert list(DoublyLinkedSet([a, b, c]) - DoublyLinkedSet([b, c, d])) == [a]

    def test_symmetric_difference(self):
        a, b, c, d = "a", "b", "c", "d"
        assert list(DoublyLinkedSet([a, b, c]) ^ DoublyLinkedSet([b, c, d])) == [a, d]

    def test_subset_superset_and_disjoint(self):
        a, b, c, d = "a", "b", "c", "d"
        full = DoublyLinkedSet([a, b, c])
        assert DoublyLinkedSet([a, b]) <= full
        assert full >= DoublyLinkedSet([a, b])
        assert DoublyLinkedSet([a, b]) < full
        assert full.isdisjoint(DoublyLinkedSet([d]))
        assert not full.isdisjoint(DoublyLinkedSet([a]))

    def test_in_place_operators(self):
        a, b, c, d = "a", "b", "c", "d"
        s = DoublyLinkedSet([a, b])
        s |= DoublyLinkedSet([c])
        assert list(s) == [a, b, c]
        s -= DoublyLinkedSet([a])
        assert list(s) == [b, c]
        s &= DoublyLinkedSet([b, d])
        assert list(s) == [b]

    def test_equality_is_order_sensitive(self):
        a, b = "a", "b"
        # Same elements and order -> equal.
        assert DoublyLinkedSet([a, b]) == DoublyLinkedSet([a, b])
        # Same elements, different order -> not equal (it is ordered).
        assert DoublyLinkedSet([a, b]) != DoublyLinkedSet([b, a])
        # Different length -> not equal.
        assert DoublyLinkedSet([a, b]) != DoublyLinkedSet([a])
        # Only another DoublyLinkedSet can compare equal.
        assert DoublyLinkedSet([a, b]) != {a, b}
        assert DoublyLinkedSet([a, b]) != [a, b]

    def test_equality_uses_identity(self):
        a = int("1000")
        b = int("1000")  # equal value, different identity
        assert DoublyLinkedSet([a]) != DoublyLinkedSet([b])

    def test_instances_are_unhashable(self):
        with pytest.raises(TypeError):
            hash(DoublyLinkedSet(["a"]))

    def test_index_and_count_use_identity(self):
        a = int("1000")
        b = int("1000")  # equal value, different identity
        s = DoublyLinkedSet(["x", a, "y"])
        assert s.index(a) == 1
        assert s.count(a) == 1
        # An equal-but-distinct object is treated as absent.
        assert s.count(b) == 0
        with pytest.raises(ValueError):
            s.index(b)

    def test_index_respects_start_stop(self):
        a, b, c = "a", "b", "c"
        s = DoublyLinkedSet([a, b, c])
        assert s.index(c, 1) == 2
        with pytest.raises(ValueError):
            s.index(a, 1)
        with pytest.raises(ValueError):
            s.index(c, 0, 2)
