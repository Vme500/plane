# Backup and Rollback Strategy

## 1. Development Environment Isolation

### 1.1 Separate Development Directory
- All AI feature development happens in `/home/qq402/projects/plane-ai-fork/plane`
- The production Plane deployment at `/home/qq402/services/plane` is **never modified**
- No shared files or configurations between dev and production

### 1.2 Branch Isolation
- All feature work happens in feature branches
- `main-ai` branch tracks `upstream/preview` (stable base)
- Feature branches are created from `main-ai`
- No direct commits to `main-ai` or `preview`

## 2. Branch Strategy

### 2.1 Branch Structure
```
upstream/preview (official Plane)
  └── main-ai (our stable base, tracks upstream)
       └── feat/ai-phase-0-setup (phase 0 documentation)
       └── feat/ai-phase-1-investigation (phase 1 code investigation)
       └── feat/ai-phase-2-feature-flags (phase 2 feature flags)
       └── feat/ai-phase-3-ui-skeleton (phase 3 UI)
       └── ... (one branch per phase)
```

### 2.2 Branch Naming Convention
- `feat/ai-phase-N-description` for feature branches
- `fix/ai-description` for bug fixes
- `docs/ai-description` for documentation-only changes

### 2.3 Merge Strategy
- Feature branches merge into `main-ai` via PR (in fork)
- `main-ai` is periodically rebased on `upstream/preview`
- Official PRs are created from `main-ai` to `upstream/preview` (when ready)

## 3. Commit Strategy

### 3.1 Commit Frequency
- Commit after each logical unit of work
- Commit at the end of each phase
- Commit before attempting risky operations

### 3.2 Commit Message Convention
```
<type>(ai): <description>

Types:
- feat: New feature
- fix: Bug fix
- docs: Documentation
- refactor: Code refactoring
- test: Tests
- chore: Maintenance
```

### 3.3 Examples
```
docs(ai): add AI assistant phase 0 planning
feat(ai): add feature flag infrastructure
feat(ai): add AI settings page skeleton
feat(ai): implement MCP client read-only tools
```

## 4. Tag Strategy

### 4.1 Backup Tags
Create tags at critical checkpoints:

```bash
# Before starting each phase
git tag backup/before-ai-phase-1
git tag backup/before-ai-phase-2
git tag backup/before-ai-phase-3
# ...

# Before risky operations
git tag backup/before-ai-settings-ui
git tag backup/before-ai-db-migration
git tag backup/before-claude-runtime
```

### 4.2 Tag Naming Convention
- `backup/before-ai-phase-N` - Before starting phase N
- `backup/before-ai-FEATURE` - Before implementing specific feature
- `v0.1.0-ai` - Release tags (when ready)

## 5. Database Backup

### 5.1 Before Migrations
Before running any database migration:
```bash
# PostgreSQL backup
pg_dump -h localhost -U plane_user plane_db > backup_pre_migration_$(date +%Y%m%d_%H%M%S).sql

# Or using Docker
docker exec plane-db pg_dump -U plane_user plane_db > backup_pre_migration_$(date +%Y%m%d_%H%M%S).sql
```

### 5.2 Migration Safety
- Always test migrations on a copy of production data first
- Migrations should be reversible (include `reverse_sql` or `down` method)
- Never run migrations on the production database during development

### 5.3 Rollback Migrations
```bash
# Django migration rollback
python manage.py migrate app_name previous_migration_name

# Or restore from backup
psql -h localhost -U plane_user plane_db < backup_file.sql
```

## 6. Docker Image Versioning

### 6.1 Image Tags
- Always use specific version tags, never `latest` in production
- Development: `plane-ai:dev-latest`
- Testing: `plane-ai:test-YYYYMMDD`
- Production: `plane-ai:v0.1.0`

### 6.2 Image Backup
```bash
# Save image to file
docker save plane-ai:v0.1.0 > plane-ai-v0.1.0.tar

# Load image from file
docker load < plane-ai-v0.1.0.tar
```

## 7. Code Rollback Procedures

### 7.1 Rollback to a Previous Branch
```bash
# Switch to main-ai
git checkout main-ai

# Delete the problematic feature branch
git branch -D feat/ai-problematic-branch

# Create a new branch from main-ai
git checkout -b feat/ai-problematic-branch-v2
```

### 7.2 Rollback to a Tag
```bash
# Create a new branch from the tag
git checkout -b rollback-branch backup/before-ai-phase-3

# Or reset main-ai to the tag (destructive!)
git checkout main-ai
git reset --hard backup/before-ai-phase-3
```

### 7.3 Rollback a Specific Commit
```bash
# Revert a specific commit (creates a new commit)
git revert <commit-hash>

# Or reset to before the commit (destructive!)
git reset --hard HEAD~1
```

## 8. Secret Safety

### 8.1 Preventing Secrets in Git
- `.gitignore` includes `.env`, `*.key`, `*.pem`, etc.
- `.env.example` uses placeholder values only
- Pre-commit hook checks for secret patterns

### 8.2 .gitignore Additions
```gitignore
# Environment files
.env
.env.local
.env.*.local

# Keys and secrets
*.key
*.pem
*.p12
*.jks

# AI-specific
ai_config.json
ai_keys.json
```

### 8.3 Pre-Commit Secret Check
```bash
# Check staged files for secrets
git diff --cached --name-only | xargs grep -l -E "(sk-ant-|sk-|api_key|secret|password|token)" && echo "WARNING: Potential secrets detected!" || echo "OK"
```

### 8.4 If a Secret is Committed
1. **Immediately rotate the secret** (generate a new one)
2. Remove the secret from Git history:
   ```bash
   # Using git-filter-repo (recommended)
   git filter-repo --path-glob '*.env' --invert-paths
   
   # Or BFG Repo-Cleaner
   bfg --delete-files .env
   ```
3. Force push (if already pushed):
   ```bash
   git push --force
   ```
4. **Note**: Anyone who has pulled the repo may have the old secret

## 9. Recovery Checklist

### 9.1 Code Issues
- [ ] Identify the problematic commit/branch
- [ ] Check if there are uncommitted changes to preserve
- [ ] Create a backup tag before rollback
- [ ] Perform rollback
- [ ] Verify rollback was successful
- [ ] Document what happened and why

### 9.2 Database Issues
- [ ] Stop the application
- [ ] Identify the problematic migration
- [ ] Check if rollback migration exists
- [ ] Restore from backup if needed
- [ ] Verify data integrity
- [ ] Restart the application
- [ ] Document what happened and why

### 9.3 Secret Exposure
- [ ] Rotate the exposed secret immediately
- [ ] Remove secret from Git history
- [ ] Force push if needed
- [ ] Audit who had access to the secret
- [ ] Check for any unauthorized usage
- [ ] Document the incident
