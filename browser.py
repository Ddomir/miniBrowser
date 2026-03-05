from lib import URL

# Parse body
def show(body):
    in_tag = False
    in_entity = False
    entity = ""

    for c in body:
        if c == "<":
            in_tag = True

        elif c == ">":
            in_tag = False

        elif in_entity:
            entity += c
            if c == ";":
                if entity == "lt;":
                    print("<", end="")
                elif entity == "gt;":
                    print(">", end="")
                else:
                    print("&" + entity, end="")
                in_entity = False
                entity = ""
                
        elif not in_tag:
            if c == "&":
                in_entity = True
            else:
                print(c, end="")



# Get content from URL and show
def load(url):
    body = url.request()
    if url.scheme == "view-source":
        print(body)
    else:
        show(body)


if __name__ == "__main__":
    import sys
    load(URL(sys.argv[1]))
