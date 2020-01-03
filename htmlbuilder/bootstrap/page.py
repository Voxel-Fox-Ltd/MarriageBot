import typing

from htmlbuilder.bootstrap.container import BootstrapContainer


class BootstrapPage(object):
    """A class representing a bootstrap page. You can add containers, to which you can add rows and columns,
    to which you can add text, etc. It _should_ all be concise enough to use, but ultimately
    it'll just conform to how I want to use it."""

    def __init__(self, title:str="Default Title"):
        self.title = title
        self.jumbotron = None
        self.containers: typing.List[BootstrapContainer] = []

    def add_container(self, container:BootstrapContainer) -> None:
        """Adds a containers to the page layout"""

        self.containers.append(container)

    def get_container(self, index:int) -> BootstrapContainer:
        """Returns the containers at the index given"""

        return self.containers[index]

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        pass

    def new_container(self) -> BootstrapContainer:
        """Gives you a new container that you can use directly in a with context"""

        container = BootstrapContainer()
        self.add_container(container)
        return container

    def to_json(self) -> dict:
        """Converts the given object into a JSON object that can be passed into the "containers.jinja" page"""

        return {
            'title': self.title,
            'jumbotron': self.jumbotron,
            'containers': [i.to_json() for i in self.containers],
        }
