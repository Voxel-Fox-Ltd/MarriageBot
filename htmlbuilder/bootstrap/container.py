import typing

from htmlbuilder.bootstrap.row import BootstrapRow


class BootstrapContainer(object):
    """Represents a container in Bootstrap. It holds things. That's about it, really."""

    def __init__(self, fluid:bool=False):
        self.rows: typing.List[BootstrapRow] = []
        self.fluid = fluid

    def add_row(self, row) -> None:
        """Adds an row to the content of the container"""

        self.rows.append(row)

    def get_row(self, index:int):
        """Gets an row from the content of the container"""

        return self.rows[index]

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        pass

    def new_row(self) -> BootstrapRow:
        """Creates and adds a new row to the container"""

        row = BootstrapRow()
        self.add_row(row)
        return row

    def to_json(self) -> dict:
        """Converts the current container object into a dictionary that can be passed into "containers.jinja"
        without issue"""

        return {
            'rows': [i.to_json() for i in self.rows],
            'fluid': self.fluid,
        }
