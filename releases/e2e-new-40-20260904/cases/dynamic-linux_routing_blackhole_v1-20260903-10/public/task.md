# Route to 2001:db8:1::/64 unreachable

Traffic to 2001:db8:1::/64 is not reaching the destination.
Ping to that subnet fails.

## Objective

Restore IPv6 route reachability to 2001:db8:1::/64.

## Success Criteria

- The declared business operation returns HTTP 200.
- The route reachability reading returns to its healthy baseline.
- The repaired behavior remains after a service restart.
