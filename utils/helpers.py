from fastapi import Request


def get_client_ip(request: Request) -> str:
    """Extract the real client IP address from request headers"""

    # Check for forwarded IP (when behind proxy/load balancer)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # Take the first IP (original client)
        return forwarded.split(",")[0].strip()

    # check for real IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # Check for CF-Connecting-IP (CloudFlare)
    cf_ip = request.headers.get("CF-Connecting-IP")
    if cf_ip:
        return cf_ip

    # Fall back to direct connection IP
    if request.client and request.client.host:
        client_ip = request.client.host

        # For development: if localhost, use a test IP for geo-analytics
        if client_ip in ["127.0.0.1", "::1"]:
            return "8.8.8.8"  # Google's IP for testing geo-analytics

        return client_ip

    # Last resort: use test IP
    return "8.8.8.8"
