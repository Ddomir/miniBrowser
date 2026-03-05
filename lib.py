import socket

class URL:

    # Split URL for obj
    def __init__(self, url):
        self.scheme, url = url.split("://", 1)
        
        # Support only http
        assert self.scheme == "http"
        
        if "/" not in url:
            url = url + "/"
        self.host, url = url.split("/", 1)
        self.path = "/" + url



    # Request data from URL
    def request(self):
        s = socket.socket(
            family=socket.AF_INET,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP,
        )

        # Connect to host
        s.connect((self.host, 80))

        # Format request
        request = "GET {} HTTP/1.0\r\n".format(self.path)
        request += "Host: {}\r\n".format(self.host)
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