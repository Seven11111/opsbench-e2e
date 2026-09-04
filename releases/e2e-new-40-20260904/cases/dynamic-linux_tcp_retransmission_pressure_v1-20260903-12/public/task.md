# Elevated TCP retransmission rate

Retransmission rate on TCP connections is above 5%
Connection latency increases due to packet loss

## Objective

Restore retransmission rate to below 1%

## Success Criteria

- The declared business operation returns HTTP 200.
- The retransmission rate reading returns to its healthy baseline.
- The repaired behavior remains after a service restart.
