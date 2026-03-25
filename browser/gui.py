
from .layout import Layout
from .html import HTMLParser
from .constants import WIDTH, HEIGHT, VSTEP, SCROLL_STEP
import tkinter
import os

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
        self.nodes = HTMLParser(body).parse()
        self.display_list = Layout(self.nodes, self.canvas.winfo_width()).display_list
        self.window.title(str(url))
        self.draw()

    def on_resize(self, e):
        if hasattr(self, "nodes"):
            self.display_list = Layout(self.nodes, e.width).display_list
            self.draw()

    def draw(self):
        self.canvas.delete("all")
        self.image_refs = []
        height = self.canvas.winfo_height()
        width = self.canvas.winfo_width()
        for x, y, word, f, img_path in self.display_list:
            if y > self.scroll + height: continue
            if y + VSTEP < self.scroll: continue
            if img_path:
                img = tkinter.PhotoImage(file=img_path).subsample(
                    max(1, 72 // VSTEP)
                )
                self.image_refs.append(img)
                self.canvas.create_image(x, y - self.scroll, image=img, anchor="nw")
            else:
                self.canvas.create_text(x, y - self.scroll, text=word, font=f, anchor="nw")

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
            self.scroll -= int(e.delta / 3)
        if self.scroll < 0:
            self.scroll = 0
        if self.display_list:
            max_y = max(y for _, y, *_ in self.display_list) + VSTEP
            height = self.canvas.winfo_height()
            self.scroll = min(self.scroll, max(0, max_y - height))
        self.draw()
