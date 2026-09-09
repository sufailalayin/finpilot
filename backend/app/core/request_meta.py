import ipaddress

from fastapi import Request


def client_ip(request: Request) -> str | None:
    peer = request.client.host if request.client else None
    if not peer:
        return None

    try:
        parsed = ipaddress.ip_address(peer)
    except ValueError:
        return peer[:64]

    if parsed.is_private or parsed.is_loopback:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            candidate = forwarded.split(",")[0].strip()
            try:
                ipaddress.ip_address(candidate)
                return candidate[:64]
            except ValueError:
                pass

    return peer[:64]


def user_agent(request: Request) -> str | None:
    value = request.headers.get("user-agent")
    return value[:500] if value else None
