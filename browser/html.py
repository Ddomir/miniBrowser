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

def resolve_entity(entity):
    """Get symbol for entity"""
    entities = {"lt": "<", "gt": ">", "amp": "&", "quot": '"',
                "apos": "'", "shy": "\N{soft hyphen}"}
    return entities.get(entity, "&" + entity + ";")



class HTMLParser:
    HEAD_TAGS = [
        "base", "basefont", "bgsound", "noscript",
        "link", "meta", "title", "style", "script",
    ]

    def __init__(self, body):
        self.body = body
        self.unfinished = []

    def parse(self):
        text = ""
        in_tag = False
        in_entity = False
        in_comment = False
        entity = ""
        for i, c in enumerate(self.body):
            if in_comment:
                if self.body[i:i+3] == "-->":
                    in_comment = False
            elif in_entity:
                if c == ";":
                    text += resolve_entity(entity)
                    in_entity = False
                    entity = ""
                else:
                    entity += c
            elif c == "<":
                if self.body[i:i+4] == "<!--":
                    in_comment = True
                    if text: self.add_text(text)
                    text = ""
                else:
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
        self.implicit_tags(None)

        parent = self.unfinished[-1]
        node = Text(text, parent)
        parent.children.append(node)

    def add_tag(self, tag):
        tag, attributes = self.get_attributes(tag)
        if tag.startswith("!"): return # DOCTYPE
        self.implicit_tags(tag)

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
            # Auto-close <p> if another is being opened
            if tag == "p" and self.unfinished and self.unfinished[-1].tag == "p":
                self.add_tag("/p")
            # Auto-close <li> (preserves nested lists)
            elif tag == "li" and self.unfinished and self.unfinished[-1].tag == "li":
                self.add_tag("/li")
            parent = self.unfinished[-1] if self.unfinished else None
            node = Element(tag, attributes, parent)
            self.unfinished.append(node)

    def finish(self):
        if not self.unfinished:
            self.implicit_tags(None)
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

    def implicit_tags(self, tag):
        while True:
            open_tags = [node.tag for node in self.unfinished]
            if open_tags == [] and tag != "html": # Implicit HTML Start
                self.add_tag("html")

            elif open_tags == ["html"] and tag not in ["head", "body", "/html"]: # Implicit Head/Body
                if tag in self.HEAD_TAGS:
                    self.add_tag("head")
                else:
                    self.add_tag("body")

            elif open_tags == ["html", "head"] and tag not in ["/head"] + self.HEAD_TAGS:
                self.add_tag("/head")

            else:
                break




def print_tree(node, indent=0, show_attrs=False):
    line = " " * indent + repr(node)
    if show_attrs and isinstance(node, Element) and node.attributes:
        attrs = " ".join(f'{k}="{v}"' if v else k for k, v in node.attributes.items())
        line += f" [{attrs}]"
    print(line)
    for child in node.children:
        print_tree(child, indent + 2, show_attrs)