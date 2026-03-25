from .constants import SELF_CLOSING_TAGS

class Text:
    """HTML Tree Leaf Node"""
    def __init__(self, text, parent=None):
        self.text = text
        self.children = []
        self.parent = parent

    def __repr__(self):
        return repr(self.text)


class Element:
    """Tag or Text Node"""
    def __init__(self, tag, attributes, parent=None):
        self.tag = tag
        self.attributes = attributes
        self.children = []
        self.parent = parent

    def get_attr(self, name):
        return self.attrs.get(name)

    def __repr__(self):
        return "<" + self.tag + ">"



def parse_attrs(raw):
    """Parse 'tag attr1="val1" attr2="val2"' into (tag, {attr: val})."""
    import re
    parts = raw.split(None, 1)
    tag = parts[0].lower() if parts else ""
    attrs = {}
    if len(parts) > 1:
        for m in re.finditer(r'([\w-]+)(?:=["\']([^"\']*)["\'])?', parts[1]):
            key = m.group(1).lower()
            attrs[key] = m.group(2) or ""
    return tag, attrs


def resolve_entity(entity):
    """Get symbol for entity"""
    entities = {"lt": "<", "gt": ">", "amp": "&", "quot": '"',
                "apos": "'", "shy": "\N{soft hyphen}"}
    return entities.get(entity, "&" + entity + ";")


class HTMLParser:
    def __init__(self, body):
        self.body = body
        self.unfinished = []

    def parse(self):
        text = ""
        in_tag = False
        in_entity = False
        entity = ""
        for c in self.body:
            if in_entity:
                if c == ";":
                    text += resolve_entity(entity)
                    in_entity = False
                    entity = ""
                else:
                    entity += c
            elif c == "<":
                in_tag = True
                if text: self.add_text(text)
                text = ""
            elif c == ">":
                in_tag = False
                self.add_tag(text)
                text = ""
            elif not in_tag and c == "&":
                in_entity = True
            else:
                text += c
        if not in_tag and text:
            self.add_text(text)
        return self.finish()

    def add_text(self, text):
        if text.isspace(): return # Ignore empty

        parent = self.unfinished[-1]
        node = Text(text, parent)
        parent.children.append(node)

    def add_tag(self, tag):
        tag, attributes = self.get_attributes(tag)
        if tag.startswith("!"): return # DOCTYPE

        if tag.startswith("/"): # close
            if len(self.unfinished) == 1: return
            node = self.unfinished.pop()
            parent = self.unfinished[-1]
            parent.children.append(node)
        
        elif tag in SELF_CLOSING_TAGS:
            parent = self.unfinished[-1]
            node = Element(tag, attributes, parent)
            parent.children.append(node)

        else: # open
            parent = self.unfinished[-1] if self.unfinished else None
            node = Element(tag, attributes, parent)
            self.unfinished.append(node)

    def finish(self):
        while len(self.unfinished) > 1:
            node = self.unfinished.pop()
            parent = self.unfinished[-1]
            parent.children.append(node)
        return self.unfinished.pop()

    def get_attributes(self, text):
        parts = text.split()
        tag = parts[0].casefold()
        attributes = {}
        for attrpair in parts[1:]:
            if "=" in attrpair:
                key, value = attrpair.split("=", 1)
                if len(value) > 2 and value[0] in ["'", "\""]: value = value[1:-1]
                attributes[key.casefold()] = value
            else:
                attributes[attrpair.casefold()] = ""
        return tag, attributes

def print_tree(node, indent=0, show_attrs=False):
    line = " " * indent + repr(node)
    if show_attrs and isinstance(node, Element) and node.attributes:
        attrs = " ".join(f'{k}="{v}"' if v else k for k, v in node.attributes.items())
        line += f" [{attrs}]"
    print(line)
    for child in node.children:
        print_tree(child, indent + 2, show_attrs)


if __name__ == "__main__":
    import sys
    from .url import URL
    if len(sys.argv) < 2:
        print("Usage: python3 -m browser.html <url>")
        sys.exit(1)
    body = URL(sys.argv[1]).request()
    tree = HTMLParser(body).parse()
    print_tree(tree)
