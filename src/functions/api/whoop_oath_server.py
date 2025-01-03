from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urlparse(self.path)
        if parsed_url.path == '/callback':
            query_components = parse_qs(parsed_url.query)
            if 'code' in query_components:
                auth_code = query_components['code'][0]
                print(f"Authorization code received: {auth_code}")
                # Exchange the authorization code for tokens here if required
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'Authorization code received. You can close this window.')
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'Missing authorization code.')
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found.')

def run_server():
    server_address = ('', 8642)
    httpd = HTTPServer(server_address, OAuthCallbackHandler)
    print('Starting server at http://localhost:8642')
    httpd.serve_forever()

if __name__ == '__main__':
    run_server()
