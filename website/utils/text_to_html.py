import re as regex


ITALICS_MATCHER = regex.compile(r"([\*_]{1,2})(.+?)[\*_]{1,2}")
LINK_MATCHER = regex.compile(r"\[(.+?)\]\((.+?)\)")


def text_to_html(lines:list) -> str:
    """Builds a HTML output from a block of lines of *basic* markdown"""

    output = []
    for line in lines:
        line = ITALICS_MATCHER.sub(lambda m: f"<i>{m.group(2)}</i>" if len(m.group(1)) == 1 else f"<b>{m.group(2)}</b>", line)
        line = LINK_MATCHER.sub(lambda m: f"<a href=\"{m.group(2)}\">{m.group(1)}</a>", line)
        output.append(f"<p>{line}</p>")
    return ''.join(output)
