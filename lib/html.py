# Parse body
def lex(body):
    in_tag = False
    in_entity = False
    entity = ""
    text = ""

    for c in body:
        if c == "<":
            in_tag = True

        elif c == ">":
            in_tag = False

        elif in_entity:
            entity += c
            if c == ";":
                if entity == "lt;":
                    text += "<"
                elif entity == "gt;":
                    text += ">"
                else:
                    text += "&" + entity
                in_entity = False
                entity = ""

        elif not in_tag:
            if c == "&":
                in_entity = True
            else:
                text += c
    
    return text
