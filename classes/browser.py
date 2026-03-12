from lib import *
import tkinter
import os

EMOJI_DIR = os.path.join(os.path.dirname(__file__), "../assets/openmoji")


def emoji_path(c):
    codepoint = "-".join(f"{ord(ch):04X}" for ch in c)
    path = os.path.join(EMOJI_DIR, codepoint + ".png")
    if os.path.exists(path):
        return path
    # fallback
    path = os.path.join(EMOJI_DIR, f"{ord(c[0]):04X}.png")
    return path if os.path.exists(path) else None

def is_emoji(c):
    cp = ord(c)
    return (
        0x1F300 <= cp <= 0x1FAFF or  # misc symbols, emoticons
        0x2600  <= cp <= 0x27BF or   # misc symbols
        0xFE00  <= cp <= 0xFE0F or   # variation selectors
        0x1F000 <= cp <= 0x1F02F     # mahjong/dominos
    )

def layout(text, width=WIDTH):
    display_list = []
    cursor_x, cursor_y = HSTEP, VSTEP
    for c in text:
        if c == "\n":
            cursor_y += VSTEP * 2
            cursor_x = HSTEP
            continue
        if is_emoji(c):
            path = emoji_path(c)
            if path:
                display_list.append((cursor_x, cursor_y, c, path))
                cursor_x += VSTEP
                if cursor_x >= width - HSTEP:
                    cursor_y += VSTEP
                    cursor_x = HSTEP
                continue
        display_list.append((cursor_x, cursor_y, c, None))
        cursor_x += HSTEP
        if cursor_x >= width - HSTEP:
            cursor_y += VSTEP
            cursor_x = HSTEP
    return display_list


class Browser:
    def __init__(self):
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(
            self.window, 
            width=WIDTH,
            height=HEIGHT
        )
        self.canvas.pack(fill="both", expand=True)
        self.scroll = 0

        # Bind keys
        self.window.bind("<Down>", self.scrolldown)
        self.window.bind("<Up>", self.scrollup)
        self.window.bind_all("<MouseWheel>", self.on_mousewheel)
        self.window.bind_all("<TouchpadScroll>", self.on_touchpad)
        self.window.bind("<Button-4>", self.on_mousewheel)
        self.window.bind("<Button-5>", self.on_mousewheel)
        self.window.bind("<Configure>", self.on_resize)
        self.canvas.bind("<Button-1>", lambda _: self.canvas.focus_set())

    def load(self, url):
        body = url.request()
        self.text = lex(body)
        self.display_list = layout(self.text, self.canvas.winfo_width())
        self.window.title(str(url))
        self.draw()

    def on_resize(self, e):
        if hasattr(self, "text"):
            self.display_list = layout(self.text, e.width)
            self.draw()

    def draw(self):
        self.canvas.delete("all")
        self.image_refs = []
        height = self.canvas.winfo_height()
        width = self.canvas.winfo_width()
        for x, y, c, img_path in self.display_list:
            if y > self.scroll + height: continue
            if y + VSTEP < self.scroll: continue
            if img_path:
                img = tkinter.PhotoImage(file=img_path).subsample(
                    max(1, 72 // VSTEP)
                )
                self.image_refs.append(img)
                self.canvas.create_image(x, y - self.scroll, image=img, anchor="nw")
            else:
                self.canvas.create_text(x, y - self.scroll, text=c, anchor="nw")

        # Draw scrollbar
        if self.display_list:
            max_y = max(y for _, y, *_ in self.display_list) + VSTEP
            if max_y > height:
                bar_height = height * (height / max_y)
                bar_top = height * (self.scroll / max_y)
                self.canvas.create_rectangle(
                    width - 8, bar_top,
                    width, bar_top + bar_height,
                    fill="blue", width=0
                )

    def scrolldown(self, e):
        if self.display_list:
            max_y = max(y for _, y, *_ in self.display_list) + VSTEP
            height = self.canvas.winfo_height()
            self.scroll = min(self.scroll + SCROLL_STEP, max_y - height)
        self.draw()
    
    def scrollup(self, e):
        if self.scroll != 0:
            self.scroll -= SCROLL_STEP

        if self.scroll < 0:
            self.scroll = 0
        self.draw()

    def on_touchpad(self, e):
        self.scroll -= int(e.delta / 5000)
        if self.scroll < 0:
            self.scroll = 0
        if self.display_list:
            max_y = max(y for _, y, *_ in self.display_list) + VSTEP
            height = self.canvas.winfo_height()
            self.scroll = min(self.scroll, max(0, max_y - height))
        self.draw()

    def on_mousewheel(self, e):
        if e.num == 4:
            self.scroll -= SCROLL_STEP
        elif e.num == 5:
            self.scroll += SCROLL_STEP
        else:
            self.scroll -= e.delta * SCROLL_STEP
        if self.scroll < 0:
            self.scroll = 0
        if self.display_list:
            max_y = max(y for _, y, *_ in self.display_list) + VSTEP
            height = self.canvas.winfo_height()
            self.scroll = min(self.scroll, max(0, max_y - height))
        self.draw()