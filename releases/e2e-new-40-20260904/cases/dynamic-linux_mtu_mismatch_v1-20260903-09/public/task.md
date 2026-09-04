# Path MTU probe failures

Path MTU probe packets are not receiving responses, causing fragmentation avoidance to fail.
Connections to certain remote hosts experience intermittent timeouts.

## Objective

Restore consistent path MTU discovery.

## Success Criteria

- The declared business operation returns HTTP 200.
- The path mtu probe reading returns to its healthy baseline.
- The repaired behavior remains after a service restart.
