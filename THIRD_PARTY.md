# Third-party components

The application runtime uses only the Python 3.12 standard library. No third-party crawler, reverse-engineering implementation, SDK, interception library, or remote API is embedded.

The `pyproject.toml` build backend is Hatchling. Hatchling is a development/build tool and retains its own license; it is not vendored or relicensed here. A later distribution review must verify the exact build environment and resulting package contents before any public release.
