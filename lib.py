import socket
import ssl

# Cache of open sockets keyed by (scheme, host, port)
_socket_cache = {}

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

        # view-source URLs
        if url.startswith("view-source:"):
            self.scheme = "view-source"
            inner = url[len("view-source:"):]
            self.inner_url = URL(inner)
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
    def request(self, headers=None, redirect_limit=10):
        if self.scheme == "data":
            return self.content

        if self.scheme == "view-source":
            return self.inner_url.request(headers=headers)

        if self.scheme == "file":
            with open(self.path, "r", encoding="utf8") as f:
                return f.read()

        cache_key = (self.scheme, self.host, self.port)
        s = _socket_cache.get(cache_key)
        if not s:
            s = socket.socket(
                family=socket.AF_INET,
                type=socket.SOCK_STREAM,
                proto=socket.IPPROTO_TCP,
            )
            s.connect((self.host, self.port))
            if self.scheme == "https":
                ctx = ssl.create_default_context()
                s = ctx.wrap_socket(s, server_hostname=self.host)
            _socket_cache[cache_key] = s

        # Format request
        request = "GET {} HTTP/1.1\r\n".format(self.path)

        #Headers
        request += "Host: {}\r\n".format(self.host) # Request Host
        request += "Connection: keep-alive\r\n" # Connection Type
        request += "User-Agent: miniBrowser\r\n" # Browser Identifier
        if headers:
            for header, value in headers.items():
                request += "{}: {}\r\n".format(header, value)
        request += "\r\n" # End of header

        # Convert to bytes and send
        s.send(request.encode("utf8"))

        # Read response as bytes to match Content-Length accurately
        response = s.makefile("rb")

        # Read first line of response
        statusline = response.readline().decode("utf8")
        version, status, explanation = statusline.split(" ", 2)

        # Map out headers with values
        response_headers = {}
        while True:
            line = response.readline().decode("utf8")
            if line == "\r\n": break
            header, value = line.split(":", 1)
            response_headers[header.casefold()] = value.strip()


        # Handle redirects
        if status.startswith("3") and "location" in response_headers:
            if redirect_limit == 0:
                raise Exception("Too many redirects")
            location = response_headers["location"]
            if location.startswith("/"):
                location = "{}://{}{}".format(self.scheme, self.host, location)
            return URL(location).request(headers=headers, redirect_limit=redirect_limit - 1)

        assert "content-encoding" not in response_headers
        if response_headers.get("transfer-encoding") == "chunked":
            body = b""
            while True:
                chunk_size = int(response.readline().decode("utf8").strip(), 16)
                if chunk_size == 0:
                    break
                body += response.read(chunk_size)
                response.read(2)  # consume trailing \r\n after each chunk
            content = body.decode("utf8")
        else:
            content_length = int(response_headers["content-length"])
            content = response.read(content_length).decode("utf8")

        return content