class CSSParser:
    def __init__(self, s):
        self.s = s
        self.i = 0

    def whitespace(self):
        """Skip whitespaces"""
        while self.i < len(self.s) and self.s[self.i].isspace():
            self.i += 1

    def word(self):
        """Count number of chars in a word"""
        start = self.i
        while self.i < len(self.s):
            if self.s[self.i].isalnum() or self.s[self.i] in "#-.%":
                self.i += 1
            else:
                break
        if not (self.i > start):
            raise Exception("Parsing error")
        return self.s[start:self.i]
    
    def literal(self, literal):
        """Check for literal chars"""
        if not (self.i < len(self.s) and self.s[self.i] == literal):
            raise Exception("Parsing error")
        self.i += 1

    def pair(self):
        """Return property and value pair from string seperated by ':'"""
        prop = self.word()
        self.whitespace()
        self.literal(":")
        self.whitespace()
        val = self.word()
        return prop.casefold(), val

    def body(self):
        """Return inner pairs into dict from property string"""
        pairs = {}
        while self.i < len(self.s):
            prop, val = self.pair()
            pairs[prop] = val
            self.whitespace()
            self.literal(";")
            self.whitespace()
        return pairs


    