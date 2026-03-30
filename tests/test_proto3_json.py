"""Test proto3 canonical JSON enum serialization.

Verifies that to_dict(proto3_json=True) uses the original .proto enum
names per the proto3 JSON spec, while to_dict() (default) preserves
the existing stripped Python names for backwards compatibility.
"""

from typing import List

import pytest

import betterproto


class Suit(betterproto.Enum):
    _proto_names_ = {
        "UNSPECIFIED": "SUIT_UNSPECIFIED",
        "HEARTS": "SUIT_HEARTS",
        "DIAMONDS": "SUIT_DIAMONDS",
        "CLUBS": "SUIT_CLUBS",
        "SPADES": "SUIT_SPADES",
    }

    UNSPECIFIED = 0
    HEARTS = 1
    DIAMONDS = 2
    CLUBS = 3
    SPADES = 4


from dataclasses import dataclass


@dataclass(eq=False, repr=False)
class Card(betterproto.Message):
    suit: "Suit" = betterproto.enum_field(1)
    value: int = betterproto.int32_field(2)


@dataclass(eq=False, repr=False)
class Hand(betterproto.Message):
    cards: List["Card"] = betterproto.message_field(1)


class TestProto3JsonSerialization:
    """to_dict(proto3_json=True) uses full proto names."""

    def test_single_enum(self):
        card = Card(suit=Suit.HEARTS, value=10)
        d = card.to_dict(proto3_json=True)
        assert d["suit"] == "SUIT_HEARTS"

    def test_default_uses_stripped_name(self):
        card = Card(suit=Suit.HEARTS, value=10)
        d = card.to_dict()
        assert d["suit"] == "HEARTS"

    def test_nested_propagates(self):
        hand = Hand(cards=[Card(suit=Suit.SPADES, value=1)])
        d = hand.to_dict(proto3_json=True)
        assert d["cards"][0]["suit"] == "SUIT_SPADES"


class TestProto3JsonDeserialization:
    """from_dict accepts both proto names and stripped names."""

    def test_accept_proto_name(self):
        card = Card().from_dict({"suit": "SUIT_HEARTS", "value": 10})
        assert card.suit == Suit.HEARTS

    def test_accept_stripped_name(self):
        card = Card().from_dict({"suit": "HEARTS", "value": 10})
        assert card.suit == Suit.HEARTS

    def test_accept_integer(self):
        card = Card().from_dict({"suit": 1, "value": 10})
        assert card.suit == Suit.HEARTS

    def test_round_trip_proto3(self):
        original = Card(suit=Suit.DIAMONDS, value=7)
        d = original.to_dict(proto3_json=True)
        restored = Card().from_dict(d)
        assert restored.suit == Suit.DIAMONDS
        assert restored.value == 7

    def test_round_trip_default(self):
        original = Card(suit=Suit.CLUBS, value=3)
        d = original.to_dict()
        restored = Card().from_dict(d)
        assert restored.suit == Suit.CLUBS


class TestEnumWithoutProtoNames:
    """Enums without _proto_names_ (backwards compat)."""

    def test_proto3_json_falls_back_to_name(self):
        """Without _proto_names_, proto3_json=True uses the Python name."""
        from tests.test_enum import Colour

        # Colour doesn't have _proto_names_, so proto_name == name
        assert Colour.RED.proto_name == "RED"
