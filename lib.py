import socket
import ssl

class URL:

    # Split URL for obj
    def __init__(self, url):
        
        # data URLs
        if url.startswith("data:"):
            self.scheme = "data"
            _, rest = url.split(":", 1)
            self.mediatype, self.content = rest.split(",", 1)
            self.host = self.port = self.path = None
            return

        # Other URLs
        self.scheme, url = url.split("://", 1)

        assert self.scheme in ["http", "https", "file"]

        if self.scheme == "file":
            self.path = url  # file:///path/to/file -> url = "/path/to/file"
            self.host = None
            self.port = None
            return

        if self.scheme == "http":
            self.port = 80
        elif self.scheme == "https":
            self.port = 443

        if "/" not in url:
            url = url + "/"
        self.host, url = url.split("/", 1)
        self.path = "/" + url

        if ":" in self.host:
            self.host, port = self.host.split(":", 1)
            self.port = int(port)

    # Request data from URL
    def request(self, headers=None):
        if self.scheme == "data":
            return self.content

        if self.scheme == "file":
            with open(self.path, "r", encoding="utf8") as f:
                return f.read()

        s = socket.socket(
            family=socket.AF_INET,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP,
        )

        # Connect to host
        s.connect((self.host, self.port))
        if self.scheme == "https":
            ctx = ssl.create_default_context()
            s = ctx.wrap_socket(s, server_hostname=self.host)

        # Format request
        request = "GET {} HTTP/1.0\r\n".format(self.path)

        #Headers
        request += "Host: {}\r\n".format(self.host) # Request Host
        request += "Connection: HTTP/1.1\r\n" # Connection Type
        request += "User-Agent: miniBrowser\r\n" # Browser Identifier
        if headers:
            for header, value in headers.items():
                request += "{}: {}\r\n".format(header, value)
        request += "\r\n" # End of header
        
        # Convert to bytes and send
        s.send(request.encode("utf8"))

        # Loops and waits for response
        response = s.makefile("r", encoding="utf8", newline="\r\n")

        # Read first line of response
        statusline = response.readline()
        version, status, explanation = statusline.split(" ", 2)

        # Map out headers with values
        response_headers = {}
        while True:
            line = response.readline()
            if line == "\r\n": break
            header, value = line.split(":", 1)
            response_headers[header.casefold()] = value.strip()

        # Check response is sent in usual encoding
        assert "transfer-encoding" not in response_headers
        assert "content-encoding" not in response_headers

        content = response.read()
        s.close()

        return content