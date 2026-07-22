# Desk pane

Live desk path:

```bash
echo "${HERMESPACE_HOME:-$HOME/.hermespace}/memory/hermespace/ACTIVE.md"
./scripts/hs show
./scripts/hs inject
# or
watch -n 2 ./scripts/hs show
```

No host-specific defaults in the package.
