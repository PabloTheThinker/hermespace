# Hermespace installed

Hermespace is a general plugin and must be enabled before its hooks load:

```bash
hermes plugins enable hermespace
hermes hermespace doctor
```

Inside a Hermes session:

```text
/hermespace status
```

Hermespace targets Hermes Agent v0.20.0+. It keeps active desks and hubs
session-scoped and injects context into the user message only.
