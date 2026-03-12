from lib.constants import *
from lib.cache import get_font
import os

EMOJI_DIR = os.path.join(os.path.dirname(__file__), "../assets/openmoji")

def emoji_path(c):
    codepoint = "-".join(f"{ord(ch):04X}" for ch in c)
    path = os.path.join(EMOJI_DIR, codepoint + ".png")
    if os.path.exists(path):
        return path
    path = os.path.join(EMOJI_DIR, f"{ord(c[0]):04X}.png")
    return path if os.path.exists(path) else None



def is_emoji(c):
    cp = ord(c)
    return (
        0x1F300 <= cp <= 0x1FAFF or
        0x2600  <= cp <= 0x27BF or
        0xFE00  <= cp <= 0xFE0F or
        0x1F000 <= cp <= 0x1F02F
    )



class Text:
    def __init__(self, text):
        self.text = text



class Tag:
    def __init__(self, tag):
        self.tag = tag



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



class Layout:
    def __init__(self, tokens, width=WIDTH):
        self.display_list = []
        self.cursor_x = HSTEP
        self.cursor_y = VSTEP
        self.weight = "normal"
        self.style = "roman"
        self.width = width
        self.size = 12
        self.line = [] # Size Calc Buffer

        for tok in tokens:
            self.token(tok)

        self.flush() # Clear Buffer



    def token(self, tok):
        if isinstance(tok, Text):
            for word in tok.text.split():
                self.word(word)

        # Italic tags
        elif tok.tag == "i":
            self.style = "italic"
        elif tok.tag == "/i":
            self.style = "roman"

        # Bold tags
        elif tok.tag == "b":
            self.weight = "bold"
        elif tok.tag == "/b":
            self.weight = "normal"

        # Small/Big tags
        elif tok.tag == "small":
            self.size -= 2
        elif tok.tag == "/small":
            self.size += 2
        elif tok.tag == "big":
            self.size += 4
        elif tok.tag == "/big":
            self.size -= 4
        
        # Break tag
        elif tok.tag == "br":
            self.flush()

        # Paragraph tag (newline)
        elif tok.tag == "/p":
            self.flush()
            self.cursor_y += VSTEP



    def word(self, word):
        # Check if the word is a single emoji character
        if len(word) >= 1 and is_emoji(word[0]):
            path = emoji_path(word[0])
            if path:
                if self.cursor_x + VSTEP > self.width - HSTEP:
                    self.flush()
                self.display_list.append((self.cursor_x, self.cursor_y, word[0], None, path))
                self.cursor_x += VSTEP + get_font(self.size, "normal", "roman").measure(" ")
                return

        f = get_font(self.size, self.weight, self.style)
        w = f.measure(word)

        if self.cursor_x + w > self.width - HSTEP:
            self.flush()

        self.line.append((self.cursor_x, word, f))
        self.cursor_x += w + f.measure(" ")



    def flush(self):
        if not self.line: return
        # Get Tallest
        metrics = [font.metrics() for x, word, font in self.line]
        max_ascent = max([metric["ascent"] for metric in metrics])

        baseline = self.cursor_y + 1.25 * max_ascent

        for x, word, font in self.line:
            y = baseline - font.metrics("ascent")
            self.display_list.append((x, y, word, font, None))
        
        # Find how for to go down next
        max_descent = max([metric["descent"] for metric in metrics])
        self.cursor_y = baseline + 1.25 * max_descent

        self.cursor_x = HSTEP
        self.line = []