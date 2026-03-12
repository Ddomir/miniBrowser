from lib import *
import tkinter


def layout(text, width=WIDTH):
    display_list = []
    cursor_x, cursor_y = HSTEP, VSTEP
    for c in text:
        if c == "\n":
            cursor_y += VSTEP * 2
            cursor_x = HSTEP
            continue
        display_list.append((cursor_x, cursor_y, c))
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
        self.window.bind("<MouseWheel>", self.on_mousewheel)
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)
        self.window.bind("<Button-4>", self.on_mousewheel)
        self.window.bind("<Button-5>", self.on_mousewheel)
        self.window.bind("<Configure>", self.on_resize)

    def load(self, url):
        body = url.request()
        self.text = lex(body)
        self.display_list = layout(self.text, self.canvas.winfo_width())
        self.draw()

    def on_resize(self, e):
        if hasattr(self, "text"):
            self.display_list = layout(self.text, e.width)
            self.draw()

    def draw(self):
        self.canvas.delete("all")
        height = self.canvas.winfo_height()
        width = self.canvas.winfo_width()
        for x, y, c in self.display_list:
            if y > self.scroll + height: continue
            if y + VSTEP < self.scroll: continue
            self.canvas.create_text(x, y - self.scroll, text=c, anchor="nw")

        # Draw scrollbar
        if self.display_list:
            max_y = max(y for _, y, _ in self.display_list) + VSTEP
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
            max_y = max(y for _, y, _ in self.display_list) + VSTEP
            height = self.canvas.winfo_height()
            self.scroll = min(self.scroll + SCROLL_STEP, max_y - height)
        self.draw()
    
    def scrollup(self, e):
        if self.scroll != 0:
            self.scroll -= SCROLL_STEP

        if self.scroll < 0:
            self.scroll = 0
        self.draw()

    def on_mousewheel(self, e):
        if e.num == 4:          # Linux scroll up
            self.scroll -= SCROLL_STEP
        elif e.num == 5:        # Linux scroll down
            self.scroll += SCROLL_STEP
        else:                   # macOS/Windows: delta is positive when scrolling up
            delta = e.delta if abs(e.delta) > 1 else e.delta * SCROLL_STEP
            self.scroll -= delta
        if self.scroll < 0:
            self.scroll = 0
        if self.display_list:
            max_y = max(y for _, y, _ in self.display_list) + VSTEP
            height = self.canvas.winfo_height()
            self.scroll = min(self.scroll, max(0, max_y - height))
        self.draw()