import tkinter.font
import tkinter
import time

# --- HTML.PY CACHES ---

# Font cache
FONTS = {}

def get_font(size, weight, style):
    key = (size, weight, style)
    if key not in FONTS:
        font = tkinter.font.Font(size=size, weight=weight, slant=style)
        label = tkinter.Label(font=font)
        FONTS[key] = (font, label)
    return FONTS[key][0]

# --- URL.PY CACHES ---

# HTTP response cache: url_str -> (content, expires_at)
_response_cache = {}

def get_cached_response(url_str):
    if url_str in _response_cache:
        content, expires_at = _response_cache[url_str]
        if expires_at is None or time.time() < expires_at:
            return content
        del _response_cache[url_str]
    return None

def cache_response(url_str, content, cache_control=""):
    directives = [d.strip() for d in cache_control.split(",")]
    known = {"no-store", "max-age"}
    directive_names = {d.split("=")[0].strip() for d in directives if d}
    if directive_names - known or "no-store" in directive_names:
        return
    expires_at = None
    for d in directives:
        if d.startswith("max-age="):
            expires_at = time.time() + int(d.split("=")[1])
    _response_cache[url_str] = (content, expires_at)
