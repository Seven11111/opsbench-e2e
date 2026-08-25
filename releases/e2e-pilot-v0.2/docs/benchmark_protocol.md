# E2E Benchmark Protocol

Flash and Pro must use the same frozen manifest, Agent entrypoint, system
prompt, tools, resource limits, timeout, and `max_steps=60`. Only the model
name changes.

Run each case once initially. Repeat timeout, infrastructure-error,
contradictory, or unstable cases three times. Report infrastructure errors
separately from Agent failures and verifier failures.
