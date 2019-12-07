import re as regex


ITALICS_MATCHER = regex.compile(r"([\*_]{1,2})(.+?)[\*_]{1,2}")
LINK_MATCHER = regex.compile(r"\[(.+?)\]\((.+?)\)")


def text_to_html(lines:list) -> str:
    """Builds a HTML output from a block of lines of *basic* markdown"""

    output = []
    tag = 'p'
    list_indent = 0
    for line in lines:
        line = ITALICS_MATCHER.sub(lambda m: f"<i>{m.group(2)}</i>" if len(m.group(1)) == 1 else f"<b>{m.group(2)}</b>", line)
        line = LINK_MATCHER.sub(lambda m: f"<a href=\"{m.group(2)}\">{m.group(1)}</a>", line)
        if line.startswith('* ') and list_indent == 0:
            output.append("<ul>")
            tag = 'li'
            list_indent += 1
            line = line[2:]
        elif line.startswith('* '):
            line = line[2:]
        elif not line.startswith('* ') and list_indent > 0:
            output.append('</ul>')
            tag = 'p'
            list_indent -= 1
        output.append(f"<{tag}>{line}</{tag}>")
    return ''.join(output)
