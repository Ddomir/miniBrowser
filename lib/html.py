from lib.constants import *
from lib.cache import get_font
from dataclasses import dataclass
from typing import Any
import os


@dataclass
class LineEntry:
    x: float
    word: str
    font: Any
    superscript: bool = False

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



class Layout:
    def __init__(self, tokens, width=WIDTH):
        self.display_list = []
        self.cursor_x = HSTEP
        self.cursor_y = VSTEP
        self.weight = "normal"
        self.style = "roman"
        self.width = width
        self.size = 12
        self.centered = False
        self.superscript = False
        self.line = []

        for tok in tokens:
            self.token(tok)

        self.flush() # Clear Buffer



    def token(self, tok):
        if isinstance(tok, Text):
            for word in tok.text.split():
                self.word(word.upper() if self.superscript else word)

        # Style tags
        elif tok.tag == "i":
            self.style = "italic"
        elif tok.tag == "/i":
            self.style = "roman"
            
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

        elif tok.tag == "h1":
            self.flush()
            self.size += 8
            if tok.get_attr("class") == "title":
                self.centered = True
        elif tok.tag == "/h1":
            self.size -= 8
            self.flush()
            self.centered = False
            self.cursor_y += VSTEP

        elif tok.tag == "sup":
            self.flush()
            self.superscript = True
            self.size = max(1, self.size // 2)
        elif tok.tag == "/sup":
            self.superscript = False
            self.size *= 2



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

        # Handle soft hyphens
        SHY = "\N{soft hyphen}"
        if SHY in word and self.cursor_x + w > self.width - HSTEP:
            chunks = word.split(SHY)
            current = ""
            for i, chunk in enumerate(chunks):
                trial = current + chunk
                trial_w = f.measure(trial + "-") if i < len(chunks) - 1 else f.measure(trial)
                if self.cursor_x + trial_w > self.width - HSTEP and current:
                    # Break here — draw current + hyphen, flush, continue with rest
                    self.line.append(LineEntry(self.cursor_x, current + "-", f, self.superscript))
                    self.cursor_x += f.measure(current + "-")
                    self.flush()
                    current = chunk
                else:
                    current = trial
            if current:
                clean = current.replace(SHY, "")
                self.line.append(LineEntry(self.cursor_x, clean, f, self.superscript))
                self.cursor_x += f.measure(clean) + f.measure(" ")
            return

        if self.cursor_x + w > self.width - HSTEP:
            self.flush()

        self.line.append(LineEntry(self.cursor_x, word.replace(SHY, ""), f, self.superscript))
        self.cursor_x += f.measure(word.replace(SHY, "")) + f.measure(" ")



    def flush(self):
        if not self.line: return
        # Get Tallest
        metrics = [e.font.metrics() for e in self.line]
        max_ascent = max(m["ascent"] for m in metrics)

        baseline = self.cursor_y + 1.25 * max_ascent

        if self.centered:
            line_width = sum(e.font.measure(e.word) + e.font.measure(" ") for e in self.line)
            start_x = (self.width - line_width) / 2
            cx = start_x
            for e in self.line:
                y = (baseline - max_ascent) if e.superscript else (baseline - e.font.metrics("ascent"))
                self.display_list.append((cx, y, e.word, e.font, None))
                cx += e.font.measure(e.word) + e.font.measure(" ")
        else:
            for e in self.line:
                y = (baseline - max_ascent) if e.superscript else (baseline - e.font.metrics("ascent"))
                self.display_list.append((e.x, y, e.word, e.font, None))
        
        # Find how for to go down next
        max_descent = max([metric["descent"] for metric in metrics])
        self.cursor_y = baseline + 1.25 * max_descent

        self.cursor_x = HSTEP
        self.line = []