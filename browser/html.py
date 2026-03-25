class Text:
    def __init__(self, text):
        self.text = text



class Tag:
    def __init__(self, tag):
        parts = tag.split(None, 1)  # split on first whitespace
        self.tag = parts[0].lower() if parts else ""
        self.attrs = parts[1] if len(parts) > 1 else ""

    def get_attr(self, name):
        import re
        m = re.search(r'{}=["\']([^"\']*)["\']'.format(name), self.attrs)
        return m.group(1) if m else None



def lex(body):
    out = []
    buffer = ""
    in_tag = False
    in_entity = False
    entity = ""
    for c in body:
        if in_entity:
            entity += c
            if c == ";":
                if entity == "lt;":
                    buffer += "<"
                elif entity == "gt;":
                    buffer += ">"
                elif entity == "shy;":
                    buffer += "\N{soft hyphen}"
                else:
                    buffer += "&" + entity
                in_entity = False
                entity = ""
        elif c == "<":
            in_tag = True
            if buffer: out.append(Text(buffer))
            buffer = ""
        elif c == ">":
            in_tag = False
            out.append(Tag(buffer))
            buffer = ""
        elif not in_tag and c == "&":
            in_entity = True
        else:
            buffer += c
    if not in_tag and buffer:
        out.append(Text(buffer))
    return out
