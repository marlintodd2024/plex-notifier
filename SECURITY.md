# Security

## Overview

BingeAlert takes security seriously. As of v1.2.0, the application includes comprehensive security hardening with 16 audit findings resolved, covering authentication, access control, input validation, and information disclosure.

## Quick Security Checklist

After installing BingeAlert, complete these steps:

- [ ] **Generate a strong `APP_SECRET_KEY`** — Used to sign session cookies
  ```bash
  python3 -c "import secrets; print(secrets.token_hex(32))"
  ```
- [ ] **Set `ENVIRONMENT=production`** — Disables API docs (default)
- [ ] **Set `WEBHOOK_ALLOWED_IPS`** — Restrict webhook sources to your Sonarr/Radarr/Seerr IP
- [ ] **Enable authentication** — Settings → Authentication & Security
- [ ] **Set admin password** — Required before enabling auth
- [ ] **Configure local network CIDR** — e.g. `192.168.1.0/24` for LAN bypass
- [ ] **Use HTTPS** — Place behind a reverse proxy with SSL/TLS
- [ ] **Configure proxy headers** — Ensure `X-Real-IP` and `X-Forwarded-For` are forwarded

## Security Features

### Authentication
- **Password-protected admin panel** — All admin endpoints require authentication via session cookie
- **Bcrypt password hashing** — Passwords are stored as bcrypt hashes, never in plaintext
- **Session token signing** — HMAC-SHA256 signed session tokens with configurable timeout (1 hour to 7 days)
- **Local network bypass** — Optional CIDR-based bypass for trusted local networks (with proper X-Forwarded-For handling behind reverse proxies)
- **Cloudflare Turnstile** — Optional bot protection on the login page (free)

### Access Control
- **Public endpoints restricted** — Only health checks, webhooks, and the login page are publicly accessible
- **API documentation disabled in production** — Swagger UI (`/docs`), ReDoc (`/redoc`), and OpenAPI schema (`/openapi.json`) return 404 when `ENVIRONMENT=production` (default)
- **Setup wizard locked after completion** — Setup pages are only accessible before initial setup is complete
- **SSE endpoints require auth** — Real-time log and notification streams are not publicly accessible

### Webhook Security
- **IP allowlisting** — Set `WEBHOOK_ALLOWED_IPS` to restrict which IPs can submit webhooks. Supports individual IPs and CIDR notation. Leave blank to allow all (backwards compatible).
  ```env
  # Single IP
  WEBHOOK_ALLOWED_IPS=192.168.1.100
  
  # Multiple IPs
  WEBHOOK_ALLOWED_IPS=192.168.1.100,192.168.1.101
  
  # CIDR range
  WEBHOOK_ALLOWED_IPS=192.168.1.0/24
  ```
- Unauthorized webhook attempts return 403 and are logged with the source IP

### Hardening
- **Login rate limiting** — 5 attempts per IP address per 5-minute window
- **Generic error messages** — Internal errors return `"Internal server error"` to clients; detailed errors are logged server-side only (49 instances hardened)
- **No secrets in API responses** — The config endpoint fully masks all API keys, passwords, and tokens
- **No secrets in backups** — Database backups never include `.env` or configuration files
- **Backup restore validation** — ZIP integrity check, required file validation, path traversal protection, file type allowlisting, 50MB size limit
- **Server header hidden** — OpenResty/nginx version header removed from responses
- **Weak secret key detection** — Logs a critical warning on startup if `APP_SECRET_KEY` is missing or uses a default value

## Recommended Production Setup

### Reverse Proxy (Required)
BingeAlert should always run behind a reverse proxy (Nginx, Nginx Proxy Manager, Traefik, etc.) that handles:
- **SSL/TLS termination** — Use HTTPS with a valid certificate (Let's Encrypt is free)
- **Client IP forwarding** — Configure your proxy to send `X-Real-IP` and `X-Forwarded-For` headers:
  ```nginx
  proxy_set_header X-Real-IP $remote_addr;
  proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  ```

**Nginx Proxy Manager** — If using NPM, you can hide the server header globally:
```bash
# Create /volume1/docker/npm/data/nginx/custom/http_top.conf
more_clear_headers 'Server';
```

### Environment Variables
- **`APP_SECRET_KEY`** — Set to a strong random string (at least 32 characters). Used to sign session cookies. **Never use the default value.**
  ```bash
  python3 -c "import secrets; print(secrets.token_hex(32))"
  ```
- **`ENVIRONMENT`** — Set to `production` (default) to disable API docs. Set to `development` only for local testing.
- **`WEBHOOK_ALLOWED_IPS`** — Comma-separated list of IPs or CIDRs allowed to send webhooks. Recommended: set to your Sonarr/Radarr/Seerr server IP.

### Network Security
- **Local network CIDR** — If using the CIDR bypass feature, use the narrowest range possible (e.g., `/32` for a single IP, `/28` for a small subnet). Avoid `/16` or larger ranges.
- **Webhook IP restriction** — Even on a local network, setting `WEBHOOK_ALLOWED_IPS` prevents other devices from submitting malicious webhooks.

## Reporting Vulnerabilities

If you discover a security vulnerability, please report it responsibly:

1. **Do not** open a public GitHub issue
2. Contact the maintainer directly at marlintodd@me.com
3. Include steps to reproduce the vulnerability
4. Allow reasonable time for a fix before public disclosure

## Security Audit History

| Version | Date | Summary |
|---------|------|---------|
| v1.2.0 | February 2026 | Full security audit — all 16 findings resolved |
| v1.0.0 | February 2026 | Initial release with basic auth middleware |

### v1.2.0 Audit Findings (All Resolved)

| ID | Severity | Finding | Resolution |
|----|----------|---------|------------|
| CRIT-0 | Critical | Auth bypass when DB unavailable (fail-open) | Changed to fail-closed (503) |
| CRIT-1 | Critical | API docs/schema publicly accessible | Disabled in production mode |
| CRIT-2 | Critical | Partial API key leakage in config endpoint | Full masking of all secrets |
| CRIT-3 | Critical | Backup downloads included .env file | Excluded from backups |
| HIGH-1 | High | No webhook source validation | IP allowlisting with CIDR support |
| HIGH-2 | High | CIDR bypass insufficient logging | Debug logging for bypass events |
| HIGH-3 | High | SSE endpoints publicly accessible | Moved behind auth middleware |
| HIGH-4 | High | Error messages leaked internal details | Generic errors (49 instances) |
| MED-1 | Medium | Setup pages accessible after completion | Locked via DB status check |
| MED-2 | Medium | Seerr webhook no validation | Covered by IP allowlisting |
| MED-3 | Medium | Weak/default APP_SECRET_KEY allowed | Startup warning for weak keys |
| MED-4 | Medium | Backup restore no input validation | Comprehensive validation added |
| MED-5 | Medium | No login rate limiting | 5 attempts per 5-minute window |
| LOW-1 | Low | Server header reveals OpenResty version | Header removed via proxy config |
| LOW-2 | Low | No HTTPS | Already enabled via proxy |
| LOW-3 | Low | .gitignore coverage gaps | Already adequate |
