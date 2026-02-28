# Security

## Overview

BingeAlert takes security seriously. As of v1.1.0, the application includes a comprehensive security layer with authentication middleware, session management, and rate limiting.

## Security Features

### Authentication
- **Password-protected admin panel** — All admin endpoints require authentication via session cookie
- **Bcrypt password hashing** — Passwords are stored as bcrypt hashes, never in plaintext
- **Session token signing** — HMAC-SHA256 signed session tokens with configurable timeout
- **Local network bypass** — Optional CIDR-based bypass for trusted local networks (with proper X-Forwarded-For handling behind reverse proxies)

### Access Control
- **Public endpoints restricted** — Only health checks, webhooks, and the login page are publicly accessible
- **API documentation disabled in production** — Swagger UI (`/docs`), ReDoc (`/redoc`), and OpenAPI schema (`/openapi.json`) are disabled by default. Set `ENVIRONMENT=development` to enable them locally.
- **Setup wizard locked after completion** — The setup pages are only accessible before initial setup is complete
- **SSE endpoints require auth** — Real-time log and notification streams are not publicly accessible

### Hardening
- **Login rate limiting** — 5 attempts per IP address per 5-minute window
- **Generic error messages** — Internal errors return `"Internal server error"` to clients; detailed errors are logged server-side only
- **No secrets in API responses** — The config endpoint never reveals any portion of API keys, passwords, or tokens
- **No secrets in backups** — Database backups never include `.env` or configuration files
- **Cloudflare Turnstile support** — Optional CAPTCHA integration for the login page

## Recommended Production Setup

### Reverse Proxy (Required)
BingeAlert should always run behind a reverse proxy (Nginx, Nginx Proxy Manager, Traefik, etc.) that handles:
- **SSL/TLS termination** — Use HTTPS with a valid certificate (Let's Encrypt is free)
- **Client IP forwarding** — Configure your proxy to send `X-Forwarded-For` and `X-Real-IP` headers:
  ```nginx
  proxy_set_header X-Real-IP $remote_addr;
  proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  ```

### Environment Variables
- **`APP_SECRET_KEY`** — Set to a strong random string (at least 32 characters). Used to sign session cookies. **Never use the default value.**
  ```bash
  # Generate a secure key:
  python3 -c "import secrets; print(secrets.token_hex(32))"
  ```
- **`ENVIRONMENT`** — Set to `production` (default) to disable API docs. Set to `development` only for local testing.

### Network Security
- **Local network CIDR** — If using the CIDR bypass feature, use the narrowest range possible (e.g., `/32` for a single IP, `/28` for a small subnet). Avoid `/16` or larger ranges.
- **Webhook endpoints** — These are intentionally public (Sonarr/Radarr/Seerr need to reach them). Consider IP allowlisting at the proxy level if your services have static IPs.

## Reporting Vulnerabilities

If you discover a security vulnerability, please report it responsibly:

1. **Do not** open a public GitHub issue
2. Contact the maintainer directly at marlintodd@me.com
3. Include steps to reproduce the vulnerability
4. Allow reasonable time for a fix before public disclosure

## Security Audit History

| Version | Date | Summary |
|---------|------|---------|
| v1.1.0 | February 2026 | Comprehensive security audit and hardening — 13 findings resolved |
| v1.0.0 | February 2026 | Initial release with basic auth middleware |
