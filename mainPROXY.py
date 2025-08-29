import network
import socket
import ure
import uasyncio as asyncio
import time

# 1. Connect to iPhone hotspot
ssid = 'iPhone'
password = 'Niktamere'

sta = network.WLAN(network.STA_IF)
sta.active(True)
sta.connect(ssid, password)

print("Connecting to hotspot...")
timeout = 15
start = time.time()
while not sta.isconnected():
    if time.time() - start > timeout:
        print("Failed to connect to hotspot.")
        break
    time.sleep(1)

if sta.isconnected():
    print("Connected to hotspot with IP:", sta.ifconfig()[0])
else:
    print("Hotspot connection failed.")

# 2. Start ESP32 Access Point
ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(essid='ESP32-Portal', authmode=network.AUTH_WPA_WPA2_PSK, password='12345678')
print("Access point active:", ap.config('essid'), ap.ifconfig())

ap_ip = ap.ifconfig()[0]

# 3. User login state
user_logged_in = False
current_user = None

# 4. Valid users
valid_users = {
    "admin": "admin123",
    "user": "pass",
    "guest": "guest"
}

class HTTPServer:
    def __init__(self, ip):
        self.ip = ip
        self.sock = socket.socket()
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('0.0.0.0', 80))
        self.sock.listen(5)
        self.sock.setblocking(False)

    async def handle_client(self, cl, addr):
        global user_logged_in, current_user
        print('Client connected from', addr)
        try:
            request = b""
            while True:
                part = cl.recv(1024)
                if not part:
                    break
                request += part
                if len(part) < 1024:
                    break
            request_str = request.decode()
        except Exception as e:
            print("Error reading request:", e)
            cl.close()
            return

        first_line = request_str.split('\n')[0]
        print("Request:", first_line)

        match_path = ure.search(r'GET\s+([^\s]+)', first_line)
        path = '/'
        if match_path:
            path = match_path.group(1).split('?')[0]

        if path == '/' or path == '/login':
            if not user_logged_in:
                response = """\
HTTP/1.1 200 OK
Content-Type: text/html
Connection: close

<!DOCTYPE html>
<html>
<head><title>Login Portal</title></head>
<body>
<h1>Login Required</h1>
<p>You must enter a valid username and password to access the internet.</p>
<form action="/submit" method="get">
    Username: <input type="text" name="user"><br>
    Password: <input type="password" name="pass"><br>
    <input type="submit" value="Login">
</form>
</body>
</html>
"""
                cl.send(response.encode())
                cl.close()
                return
            else:
                response = "HTTP/1.1 302 Found\r\nLocation: /proxy\r\nConnection: close\r\n\r\n"
                cl.send(response.encode())
                cl.close()
                return

        elif path.startswith('/submit'):
            match_user = ure.search(r'user=([^&]+)', request_str)
            match_pass = ure.search(r'pass=([^&\s]+)', request_str)

            if match_user and match_pass:
                username = match_user.group(1)
                password = match_pass.group(1)

                if username in valid_users and valid_users[username] == password:
                    user_logged_in = True
                    current_user = username
                    print("Login successful for user:", username)
                    response = """\
HTTP/1.1 200 OK
Content-Type: text/html
Connection: close

<!DOCTYPE html>
<html>
<head><title>Login Success</title></head>
<body>
<h1>Welcome {}</h1>
<p>You are now connected to the internet through the proxy.</p>
<p><a href="/proxy">Go to Proxy</a></p>
<p><a href="/logout">Logout</a></p>
</body>
</html>
""".format(username)
                else:
                    response = """\
HTTP/1.1 200 OK
Content-Type: text/html
Connection: close

<!DOCTYPE html>
<html>
<head><title>Login Failed</title></head>
<body>
<h1>Invalid Credentials</h1>
<p>Incorrect username or password.</p>
<p><a href="/login">Try Again</a></p>
</body>
</html>
"""
            else:
                response = """\
HTTP/1.1 400 Bad Request
Content-Type: text/html
Connection: close

<!DOCTYPE html>
<html>
<head><title>Bad Request</title></head>
<body>
<h1>Missing Parameters</h1>
<p>Username and password are required.</p>
<p><a href="/login">Back to Login</a></p>
</body>
</html>
"""

            cl.send(response.encode())
            cl.close()
            return

        elif path == '/logout':
            print("User logged out:", current_user)
            user_logged_in = False
            current_user = None
            response = """\
HTTP/1.1 200 OK
Content-Type: text/html
Connection: close

<!DOCTYPE html>
<html>
<head><title>Logged Out</title></head>
<body>
<h1>You have been logged out</h1>
<p><a href="/login">Login again</a></p>
</body>
</html>
"""
            cl.send(response.encode())
            cl.close()
            return

        elif path == '/proxy':
            if not user_logged_in:
                response = "HTTP/1.1 302 Found\r\nLocation: /login\r\nConnection: close\r\n\r\n"
                cl.send(response.encode())
                cl.close()
                return

            response = """\
HTTP/1.1 200 OK
Content-Type: text/html
Connection: close

<!DOCTYPE html>
<html>
<head><title>HTTP Proxy</title></head>
<body>
<h1>Proxy Access</h1>
<p>Logged in as: <strong>{}</strong></p>
<p>Configure your browser to use this HTTP proxy:</p>
<ul>
<li>Address: {}</li>
<li>Port: 80</li>
</ul>
<p>Note: Only HTTP traffic is supported (HTTPS is not supported).</p>
<p><a href="/logout">Logout</a></p>
</body>
</html>
""".format(current_user, self.ip)
            cl.send(response.encode())
            cl.close()
            return

        if user_logged_in:
            match = ure.search(r'GET\s+(http://[^\s]+)', first_line)
            if match:
                url = match.group(1)
                print("Proxying URL:", url)

                try:
                    url_no_proto = url[len("http://"):]
                    parts = url_no_proto.split("/", 1)
                    host = parts[0]
                    path_url = "/" + parts[1] if len(parts) > 1 else "/"
                except Exception as e:
                    print("URL parsing error:", e)
                    cl.send(b"HTTP/1.1 400 Bad Request\r\nConnection: close\r\n\r\n")
                    cl.close()
                    return

                try:
                    remote = socket.socket()
                    remote.connect((host, 80))
                    new_request = "GET {} HTTP/1.1\r\nHost: {}\r\nConnection: close\r\n\r\n".format(path_url, host)
                    remote.send(new_request.encode())

                    while True:
                        data = remote.recv(512)
                        if not data:
                            break
                        cl.send(data)
                except Exception as e:
                    print("Proxy error:", e)
                    cl.send(b"HTTP/1.1 502 Bad Gateway\r\nContent-Type: text/plain\r\n\r\nProxy error")
                finally:
                    remote.close()
                    cl.close()
                    return
            else:
                cl.send(b"HTTP/1.1 400 Bad Request\r\nConnection: close\r\n\r\n")
                cl.close()
                return
        else:
            response = "HTTP/1.1 302 Found\r\nLocation: /login\r\nConnection: close\r\n\r\n"
            cl.send(response.encode())
            cl.close()

    async def run(self):
        print('HTTP server running at http://{}/'.format(self.ip))
        while True:
            try:
                cl, addr = self.sock.accept()
            except OSError:
                await asyncio.sleep_ms(10)
                continue
            await self.handle_client(cl, addr)

async def main():
    http = HTTPServer(ap_ip)
    await http.run()

try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("Shutdown requested.")

