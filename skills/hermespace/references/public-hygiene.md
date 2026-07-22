# Public package hygiene

## Rules
- No secrets, tokens, `.env`, auth material in git  
- No personal names, private emails, wages, family, clinical data  
- No operator host fingerprints (absolute home paths, tailnet IPs, internal hostnames)  
- Desk state (`ACTIVE.md`, episodes, seals, DB, journal, workbenches) stays **out of git**  
- State root: `HERMESPACE_HOME` or `~/.hermespace`  

## Before push
```bash
./scripts/security_audit.sh
./scripts/smoke_test.sh    # or unittest
```

1. security_audit OK  
2. smoke or unit tests green  
3. no operator paths in tracked files  
4. commit messages feature-level (no host details)  
5. skill + plugin versions coherent with package  

See repo `SECURITY.md`.  
