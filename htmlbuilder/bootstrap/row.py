import typing

from htmlbuilder.bootstrap.column import BootstrapColumn


class BootstrapRow(object):
    """Represents a row in Bootstrap. It holds columns. That's about it."""

    def __init__(self):
        self.columns: typing.List[BootstrapColumn] = []

    def add_column(self, column:BootstrapColumn) -> None:
        """Adds an column to the content of the container"""

        self.columns.append(column)

    def get_column(self, index:int):
        """Gets an item from the content of the container"""

        return self.columns[index]

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        pass

    def new_column(self, text:str="", widths:dict=dict()) -> BootstrapColumn:
        """Creates and adds a new column to the row"""

        column = BootstrapColumn(text=text, widths=widths)
        self.add_column(column)
        return column

    def to_json(self) -> dict:
        """Converts the current container object into a dictionary that can be passed into "containers.jinja"
        without issue"""

        return {
            'columns': [i.to_json() for i in self.columns]
        }
