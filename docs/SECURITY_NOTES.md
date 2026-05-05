# Security Notes

## Scope

This repository is a research codebase for QAOA spin-physics experiments. It does not manage customer data, financial accounts, or a production credential lifecycle inside the experiment loop.

## What was removed

- Placeholder secret-handling helpers were removed because they did not protect any real secret-bearing path.
- Secure-buffer utilities were removed for the same reason: they added complexity without improving the scientific artifact.

## What remains relevant

- Public exports are explicit through module-level `__all__`.
- Logging is centralized through `logger.py` instead of raw `print(...)` calls.
- Runtime-facing code may still expect external credentials if the user chooses live Qiskit Runtime backends, but credential handling is delegated to the environment/runtime toolchain rather than simulated inside the package.

## Why this matters for review

The goal is not to make the repository look “hardened” in ways that do not map to the actual problem. The safer research posture is to keep the package narrow, understandable, and honest about what it does and does not secure.
