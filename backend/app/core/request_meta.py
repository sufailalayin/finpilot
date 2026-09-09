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
            candidates = [
                item.strip()
                for item in forwarded.split(",")
                if item.strip()
            ]
            for candidate in reversed(candidates):
                try:
                    forwarded_ip = ipaddress.ip_address(candidate)
                except ValueError:
                    continue
                if not (
                    forwarded_ip.is_private
                    or forwarded_ip.is_loopback
                    or forwarded_ip.is_link_local
                ):
                    return candidate[:64]

    return peer[:64]


def user_agent(request: Request) -> str | None:
    value = request.headers.get("user-agent")
    return value[:500] if value else None
