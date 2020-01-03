import typing

from htmlbuilder.bootstrap.card_deck import BootstrapCardDeck


class BootstrapColumn(object):
    """Represents a row in Bootstrap. It holds columns. That's about it."""

    def __init__(self, text:str="", widths:dict=dict()):
        self.text: str = text
        self.widths = widths
        self.card_decks: typing.List[BootstrapCardDeck] = []

    def add_card_deck(self, card_deck) -> None:
        """Adds a card deck to the content of the container"""

        self.card_decks.append(card_deck)

    def get_card_deck(self, index:int):
        """Gets a card deck from the content of the container"""

        return self.card_decks[index]

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        pass

    def new_card_deck(self, deck_type:str='columns') -> BootstrapCardDeck:
        """Creates a new card deck for you to use"""

        deck = BootstrapCardDeck(deck_type=deck_type)
        self.add_card_deck(deck)
        return deck

    def to_json(self) -> dict:
        """Converts the current container object into a dictionary that can be passed into "containers.jinja"
        without issue"""

        return {
            'text': self.text,
            'widths': self.widths,
            'card_decks': [i.to_json() for i in self.card_decks]
        }
