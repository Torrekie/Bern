# Download helper — static preflight

`github-ci.py` SHA256 `ae29c7de03fb3197e5107986c19ab68b39975dcd0ab9d63b6f3b2202015bbeb7` has no remaining blocking static finding in the reviewed download scope. The original literal-name duplicate guard admitted destination aliases; the final Path/NFC/casefold destination set closes that finding before extraction.

Actual ZIP hashing and API digest equality precede extraction/deletion. A mismatch preserves ZIP plus initial sibling receipt; missing API digest remains explicitly unverified. Path traversal, destination aliases and symlink/special member types are rejected, with declared expanded size below100MiB.

This review only parsed/read source and checked ordering. It never imported or ran the helper, acquired auth, accessed network/UI, or exercised a real ZIP. Assumes ordinary assertion-enabled Python and an owned fresh namespace. Failed extraction may retain a partial directory/ZIP; only the success path deletes the archive and finalizes its receipt. Future actual downloads still need their own evidence. No old cohort outer digest result is changed.
