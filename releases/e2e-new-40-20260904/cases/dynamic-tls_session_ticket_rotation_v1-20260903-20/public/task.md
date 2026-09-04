# TLS handshake failures with ticket decode errors

Clients receive TLS handshake failure with 'ticket decode error' message.
Ticket key age metric shows value exceeding 1 hour.

## Objective

Restore successful TLS handshakes for ticket-based sessions.

## Success Criteria

- The declared business operation returns HTTP 200.
- The ticket key age reading returns to its healthy baseline.
- The repaired behavior remains after a service restart.
