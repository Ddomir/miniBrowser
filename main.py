from lib import URL

# example.org typically sends gzip when Accept-Encoding: gzip is sent
url = URL("http://example.org/")
content = url.request()
print(content[:200])
print("\n--- fetched successfully (gzip decompressed if server sent it) ---")
