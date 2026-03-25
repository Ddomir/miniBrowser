from browser import URL, Browser
from browser.html import HTMLParser, print_tree
import tkinter

if __name__ == "__main__":
    import sys
    args = sys.argv[1:]

    if "--debug-tree-attrs" in args:
        args.remove("--debug-tree-attrs")
        body = URL(args[0]).request()
        print_tree(HTMLParser(body).parse(), show_attrs=True)
    elif "--debug-tree" in args:
        args.remove("--debug-tree")
        body = URL(args[0]).request()
        print_tree(HTMLParser(body).parse())
    else:
        Browser().load(URL(args[0]))
        tkinter.mainloop()
