class BootstrapCard(object):

    def __init__(self, title:str="", text:str=""):
        self.title = title
        self.text = text

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        pass

    def to_json(self) -> dict:
        """Converts the current object into a json object"""

        return {
            'title': self.title,
            'text': self.text,
        }
