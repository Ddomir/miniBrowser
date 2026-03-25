import re
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
    FORMATTING_TAGS = {"b", "i", "u", "s", "em", "strong", "small", "big", "sup", "abbr"}

    HEAD_TAGS = [
        "base", "basefont", "bgsound", "noscript",
        "link", "meta", "title", "style", "script",
    ]

    def __init__(self, body):
        self.body = body
        self.unfinished = []

    SCRIPT_END = re.compile(r"</script[\s\t\v\r/>]", re.IGNORECASE)

    def parse(self):
        text = ""
        in_tag = False
        in_attr_quote = None  # None, '"', or "'"
        in_entity = False
        in_comment = False
        in_script = False
        entity = ""
        i = 0
        while i < len(self.body):
            c = self.body[i]
            if in_script:
                m = self.SCRIPT_END.search(self.body, i)
                if m:
                    end = self.body.index(">", m.start())
                    self.add_tag(self.body[m.start()+1:end])
                    i = end + 1
                else:
                    i = len(self.body)
                in_script = False
                text = ""
                continue
            elif in_comment:
                if self.body[i:i+3] == "-->":
                    in_comment = False
                    i += 3
                else:
                    i += 1
                continue
            elif in_entity:
                if c == ";":
                    text += resolve_entity(entity)
                    in_entity = False
                    entity = ""
                else:
                    entity += c
            elif in_tag and in_attr_quote:
                if c == in_attr_quote:
                    in_attr_quote = None
                text += c
            elif c == "<":
                if self.body[i:i+4] == "<!--":
                    in_comment = True
                    if text: self.add_text(text)
                    text = ""
                    i += 4
                    continue
                else:
                    in_tag = True
                    if text: self.add_text(text)
                    text = ""
            elif c == ">":
                in_tag = False
                tag_name = text.split()[0].lower() if text.split() else ""
                self.add_tag(text)
                text = ""
                if tag_name == "script":
                    in_script = True
                i += 1
                continue
            elif in_tag and c in ('"', "'"):
                in_attr_quote = c
                text += c
            elif not in_tag and c == "&":
                in_entity = True
            else:
                text += c
            i += 1
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
            close_tag = tag[1:]
            # if closing a formatting tag that isn't on top, implicitly close everything above it, close it, then re-open them.
            if close_tag in self.FORMATTING_TAGS:
                open_tags = [node.tag for node in self.unfinished]
                if close_tag in open_tags and open_tags[-1] != close_tag:
                    popped = []
                    while self.unfinished[-1].tag != close_tag:
                        top = self.unfinished[-1]
                        if top.tag in self.FORMATTING_TAGS:
                            popped.append(top)
                        node = self.unfinished.pop()
                        parent = self.unfinished[-1]
                        parent.children.append(node)
                    node = self.unfinished.pop()
                    parent = self.unfinished[-1]
                    parent.children.append(node)
                    for reopen in reversed(popped):
                        new_node = Element(reopen.tag, reopen.attributes, self.unfinished[-1])
                        self.unfinished.append(new_node)
                    return
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
    """Used in debug-mode and debug-mode-attrs"""
    line = " " * indent + repr(node)
    if show_attrs and isinstance(node, Element) and node.attributes:
        attrs = " ".join(f'{k}="{v}"' if v else k for k, v in node.attributes.items())
        line += f" [{attrs}]"
    print(line)
    for child in node.children:
        print_tree(child, indent + 2, show_attrs)



def _escape(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

class ViewSourceParser(HTMLParser):
    """Subclass that walks parsed source HTML and emits syntax-highlighted HTML."""

    def highlight(self):
        out = ["<pre>"]
        self._walk(self.parse(), out)
        out.append("</pre>")
        return "".join(out)

    def _walk(self, node, out):
        if isinstance(node, Text):
            out.append("<b>" + _escape(node.text) + "</b>")
        else:
            # Reconstruct opening tag in normal font
            attrs = "".join(
                f' {k}="{_escape(v)}"' if v else f" {k}"
                for k, v in node.attributes.items()
            )
            out.append(_escape(f"<{node.tag}{attrs}>"))
            for child in node.children:
                self._walk(child, out)
            if node.tag not in SELF_CLOSING_TAGS:
                out.append(_escape(f"</{node.tag}>"))
