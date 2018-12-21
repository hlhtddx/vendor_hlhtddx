'''
Simple http server for Angular.
'''

import http.server
import os
import socketserver

PORT = 8000


class AngularHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def send_head(self):
        path = self.translate_path(self.path)
        # Return top index.html if request file not exist, or 404 will return
        # when refresh browser. This will work fine with router of Angular.
        if not os.path.isfile(path):
            self.path = '/'
        return super(AngularHTTPRequestHandler, self).send_head()


Handler = AngularHTTPRequestHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    httpd.serve_forever()
