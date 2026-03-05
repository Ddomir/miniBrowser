from lib import URL

def main():
    body = URL("http://example.org/index.html").request()
    print(body)

if __name__ == "__main__":
    main()
