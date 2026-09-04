# Elevated HTTP 413 response rate

Nginx returns 413 errors for POST requests with payloads under the expected limit.
Body limit rejection count is above the normal baseline.

## Objective

Restore baseline acceptance of client requests without body size rejections.

## Success Criteria

- The declared business operation returns HTTP 200.
- The body limit rejections reading returns to its healthy baseline.
- The repaired behavior remains after a service restart.
