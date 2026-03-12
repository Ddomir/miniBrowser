import gzip
import socket
import ssl
from lib.cache import get_cached_response, cache_response

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

        # about:blank and malformed URLs
        try:
            self.scheme, url = url.split("://", 1)
        except ValueError:
            self.scheme = "about"

        if self.scheme == "about" or self.scheme not in ["http", "https", "file"]:
            self.scheme = "about"
            self.host = self.port = self.path = None
            return

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

    def __str__(self):
        if self.scheme == "about":
            return "about:blank"
        if self.scheme == "data":
            return "data:{},{}".format(self.mediatype, self.content)
        if self.scheme == "view-source":
            return "view-source:{}".format(self.inner_url)
        if self.scheme == "file":
            return "file://{}".format(self.path)
        port_str = ":{}".format(self.port) if (
            (self.scheme == "http" and self.port != 80) or
            (self.scheme == "https" and self.port != 443)
        ) else ""
        return "{}://{}{}{}".format(self.scheme, self.host, port_str, self.path)

    # Request data from URL
    def request(self, headers=None, redirect_limit=10):
        if self.scheme == "about":
            return ""

        if self.scheme == "data":
            return self.content

        if self.scheme == "view-source":
            return self.inner_url.request(headers=headers)

        if self.scheme == "file":
            with open(self.path, "r", encoding="utf8") as f:
                return f.read()

        # Check response cache
        url_str = "{}://{}:{}{}".format(self.scheme, self.host, self.port, self.path)
        cached = get_cached_response(url_str)
        if cached: return cached

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
        request += "Accept-Encoding: gzip\r\n"
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

        if response_headers.get("transfer-encoding") == "chunked":
            body = b""
            while True:
                chunk_size = int(response.readline().decode("utf8").strip(), 16)
                if chunk_size == 0:
                    break
                body += response.read(chunk_size)
                response.read(2)  # consume trailing \r\n after each chunk
        else:
            content_length = int(response_headers["content-length"])
            body = response.read(content_length)

        if response_headers.get("content-encoding") == "gzip":
            body = gzip.decompress(body)

        content = body.decode("utf8")

        # Cache the response if status is 200
        if status == "200":
            cache_response(url_str, content, response_headers.get("cache-control", ""))

        return content