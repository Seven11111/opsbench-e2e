# Messages are waiting

RabbitMQ is healthy, but ready messages keep accumulating behind a live consumer.

## Objective

Restore the live service and verify the technology signal.

## Success Criteria

- The business operation returns HTTP 200.
- The declared queue backlog returns to its healthy range.
- Message delivery continues after restart.

Use only the provided bounded runtime tools. Do not replace the service or bypass validation.
