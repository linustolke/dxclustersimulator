description = """Simulates a DXCluster with a massive amount of generated spots.

These are not real spots, these are randomly generated both in turns
of call, frequency and spotter."""

import random
import socket
import string
from time import strftime, gmtime, sleep

r = random.Random()
bands = [" 18", " 19",
         " 35", " 36", " 37",
         " 70", " 71", " 70", " 71",
         "140", "141", "140", "141",
         "210", "211", "210",
         "280", "281",]
digits = [str(x) for x in range(10)]
freq_within_band = ["0" + x for x in digits] + [str(x) for x in range(10, 100)]

def generate_frequency():
    "Returns a randomly generated frequency"
    global r, bands
    return (r.choice(bands) +
            r.choice(freq_within_band) +
            "." +
            r.choice(digits))

def generate_call():
    "Returns a randomly generated call"
    global r
    return (r.choice(string.ascii_uppercase) +
            r.choice(string.ascii_uppercase) +
            r.choice(digits) +
            r.choice(string.ascii_uppercase) +
            r.choice(string.ascii_uppercase) +
            r.choice(string.ascii_uppercase))

class CQ(object):
    """Represents a randomly generated CQ.

    This is part of the information of a spot."""

    latest = list()

    def __init__(self):
        self.freq = generate_frequency()
        self.call = generate_call()
        self.speed = str(r.randint(17, 40))
        CQ.latest.append(self)
        new_latest_list_length = r.randint(10, 100)
        if new_latest_list_length < len(CQ.latest):
            CQ.latest = r.sample(CQ.latest, new_latest_list_length)

# Create a socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Ensure that you can restart your server quickly when it terminates
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Set the client socket's TCP "well-known port" number
well_known_port = 8881
sock.bind(('', well_known_port))

# Set the number of clients waiting for connection that can be queued
sock.listen(1)

print(description)
print("Listening on port", well_known_port)

# loop waiting for connections (terminate with Ctrl-C)
try:
    while 1:
        newSocket, address = sock.accept(  )
        # loop serving the new client
        newSocket.send(description.encode())
        newSocket.send(b"\nCall: ")
        receivedData = newSocket.recv(1024) 
        print("Connected from", address, "by", receivedData.decode().strip())
        newSocket.setblocking(False)
        count = 0
        blocking_sleep_time = 0.1
        while 1:
            try:
                receivedData = newSocket.recv(1024, socket.SOCK_NONBLOCK)
                if not receivedData: break
            except BlockingIOError:
                pass

            # Echo back the same data you just received
            try:
                CQ()
                spotter = generate_call()
                for cq in r.sample(CQ.latest, r.randint(1, len(CQ.latest))):
                    newSocket.send("DX de {spotter}-#:   {freq}  {dx}       CW  {db} dB   {speed} WPM  CQ   {time}Z\r\n".format(
                        spotter=spotter,
                        freq=cq.freq,
                        dx=cq.call,
                        db=str(r.randint(10, 25)),
                        speed=cq.speed,
                        time=strftime("%H%M", gmtime())).encode())
                    count += 1
                    if count % 100000 == 0:
                        print("Sent", count, "spots")
                    blocking_sleep_time = 0.1
            except BlockingIOError:
                sleep(blocking_sleep_time)
                print("Blocked waiting", blocking_sleep_time)
                blocking_sleep_time += 0.1
                if blocking_sleep_time > 2:
                    break
            except BrokenPipeError:
                break
        newSocket.close(  )
        print("Disconnected from", address, "after", count, "spots")
finally:
    sock.close(  )
