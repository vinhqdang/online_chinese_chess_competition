import socket


def get_local_ip():
    """Best-effort LAN IP address for display in the admin UI.

    Uses a connect() on a UDP socket (no packets actually sent) purely to
    ask the OS which local interface/address would be used to reach the
    public internet; falls back to loopback if that's not possible (e.g.
    fully offline host).
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except OSError:
        try:
            return socket.gethostbyname(socket.gethostname())
        except OSError:
            return "127.0.0.1"
    finally:
        s.close()
