# CharterLock Architecture

```text
Request -> Classify -> Verify Source -> Enforce Policy -> Transliterate or Deny
        -> Audit Receipt -> Human Approval -> Protected Release
```

## Operating boundary

Only approved transliteration from provenance-bearing sources is permitted.
Translation, interpretation, publication, deployment, and policy changes require separate human authorization.
