import typing

from htmlbuilder.bootstrap.card import BootstrapCard


class BootstrapCardDeck(object):

    def __init__(self, deck_type:str='columns'):
        self.deck_type = deck_type  # one of 'columns' or 'deck'
        self.cards: typing.List[BootstrapCard] = []

    def add_card(self, card) -> None:
        """Adds an card to the content of the container"""

        self.cards.append(card)

    def get_card(self, index:int):
        """Gets an card from the content of the container"""

        return self.cards[index]

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        pass

    def new_card(self, title:str="", text:str="") -> BootstrapCard:
        """Creates and adds a new card to the container"""

        card = BootstrapCard(title=title, text=text)
        self.add_card(card)
        return card

    def to_json(self) -> dict:
        """Converts the current deck object into a dictionary that can be passed into "containers.jinja"
        without issue"""

        return {
            'type': self.deck_type,
            'cards': [i.to_json() for i in self.cards],
        }

