from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urlparse(self.path)
        if parsed_url.path == '/callback':
            query_components = parse_qs(parsed_url.query)
            print(f"Received query parameters: {query_components}")

            auth_code = query_components.get('code', [None])[0]
            state = query_components.get('state', [None])[0]

            # Validate the state parameter
            expected_state = "your_saved_state_value"  # Replace with your generated state
            if state != expected_state:
                print("State parameter mismatch.")
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"State parameter mismatch.")
                return

            if auth_code:
                print(f"Authorization code received: {auth_code}")
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"Authorization code received. You can close this window.")
            else:
                print("Authorization code is missing.")
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Missing authorization code.")
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found.")

def run_server():
    server_address = ('', 8642)
    httpd = HTTPServer(server_address, OAuthCallbackHandler)
    print('Starting server at http://localhost:8642')
    httpd.serve_forever()

if __name__ == '__main__':
    run_server()
