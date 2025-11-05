# Performance Analysis: API Endpoint Latency Issues

## Executive Summary

In production, several API endpoints including `/users/me`, `/transcriptions-metadata`, and others are experiencing **p95 and p99 latencies up to 20 seconds**. This analysis identifies **5 critical performance bottlenecks** and provides actionable solutions.

---

## Critical Performance Issues Identified

### 1. 🔴 **N+1 Query Problem in `/transcriptions-metadata`**

**Severity:** CRITICAL  
**Impact:** Every user with transcriptions triggers multiple database queries  
**Location:** `backend/app/database/interface_functions.py:108-129`

#### Problem

The `fetch_transcriptions_metadata()` function exhibits a classic N+1 query pattern:

```python
def fetch_transcriptions_metadata(user_id: UUID, tz) -> list[TranscriptionMetadata]:
    with Session(engine) as session:
        statement = select(Transcription).where(Transcription.user_id == user_id)
        transcriptions = session.exec(statement).all()  # 1 query
        
        return [
            TranscriptionMetadata(
                # ...
                is_showable_in_ui=_is_transcription_showable(t, current_time),  # Accesses t.minute_versions ❌
                speakers=_extract_unique_speakers(t),  # Accesses t.transcription_jobs ❌
            )
            for t in transcriptions  # N queries!
        ]
```

**For a user with 50 transcriptions, this executes:**
- 1 query to fetch transcriptions
- 50 queries to fetch `minute_versions` (lazy loading)
- 50 queries to fetch `transcription_jobs` (lazy loading)
- **Total: 101 queries** 🔥

#### Solution

Use SQLAlchemy eager loading with `selectinload()`:

```python
from sqlalchemy.orm import selectinload

def fetch_transcriptions_metadata(user_id: UUID, tz) -> list[TranscriptionMetadata]:
    with Session(engine) as session:
        statement = (
            select(Transcription)
            .where(Transcription.user_id == user_id)
            .options(
                selectinload(Transcription.minute_versions),
                selectinload(Transcription.transcription_jobs)
            )
        )
        transcriptions = session.exec(statement).all()  # Now loads everything in 3 queries total
        # ... rest of code
```

**Expected Improvement:** 97% reduction in database queries (101 → 3 queries)

---

### 2. 🔴 **Missing Database Indexes on Foreign Keys**

**Severity:** CRITICAL  
**Impact:** Full table scans on foreign key lookups  
**Location:** `backend/alembic/versions/de7d26bcb326_.py`

#### Problem

The database schema is missing indexes on critical foreign key columns:

**Missing Indexes:**
```sql
-- transcription table
transcription.user_id  -- NO INDEX ❌

-- minuteversion table  
minuteversion.transcription_id  -- NO INDEX ❌

-- transcriptionjob table
transcriptionjob.transcription_id  -- NO INDEX ❌
```

**Impact:**
- Queries like `WHERE transcription.user_id = ?` do full table scans
- As the database grows, these scans become exponentially slower
- In production with thousands of transcriptions, this is devastating

#### Current Indexes (from migrations)

Only these indexes exist:
```sql
CREATE INDEX ix_user_email ON user(email);
CREATE UNIQUE INDEX ix_user_azure_user_id ON user(azure_user_id);
```

#### Solution

Create a new migration to add missing indexes:

```sql
CREATE INDEX ix_transcription_user_id ON transcription(user_id);
CREATE INDEX ix_minuteversion_transcription_id ON minuteversion(transcription_id);
CREATE INDEX ix_transcriptionjob_transcription_id ON transcriptionjob(transcription_id);
```

**Expected Improvement:** 10-100x faster queries on foreign key lookups

---

### 3. 🟡 **Azure Blob Storage Call on Every Allowlist Check**

**Severity:** HIGH  
**Impact:** Network latency + Azure throttling on high traffic  
**Location:** `backend/utils/allowlist.py:407-471`

#### Problem

The allowlist check hits Azure Blob Storage on every request that uses `get_allowlisted_user()`:

**Flow:**
1. User makes request to `/transcriptions-metadata`
2. `get_allowlisted_user()` dependency is called
3. Checks cache (TTL: 300s = 5 minutes)
4. If cache expired or user not cached:
   - Downloads entire CSV from Azure Blob Storage (network call)
   - Parses CSV (CPU intensive)
   - Validates data (CPU intensive)

**Cold Cache Scenario:**
- Azure Blob Storage download: **200-1000ms**
- CSV parsing + validation: **50-200ms**
- Total: **250-1200ms per request**

**Issues:**
- Cache is per-user, so first request for any user is slow
- Cache expires every 5 minutes, causing periodic slowdowns
- Azure Blob Storage has rate limits (could cause 503 errors)

#### Current Caching Strategy

```python
class UserAllowlistCache:
    def __init__(self, ttl_seconds: int = 300):  # 5 minute TTL
        self._user_status: dict[str, bool] = {}
        self._expires_at: float = 0.0
        self._allowlist_data: pd.DataFrame | None = None
```

Problems:
- Global cache expires all at once (thundering herd)
- No warmup mechanism
- No fallback if Azure is slow

#### Solution

**A) Increase cache TTL:**
```python
# In settings or config
ALLOWLIST_CACHE_TTL_SECONDS = 1800  # 30 minutes instead of 5
```

**B) Pre-warm cache on startup:**
```python
# In main.py startup event
@app.on_event("startup")
async def warmup_allowlist_cache():
    """Pre-load allowlist cache to avoid cold starts"""
    try:
        cache = get_allowlist_cache()
        await cache._load_allowlist_data(...)
        logger.info("✅ Allowlist cache pre-warmed")
    except Exception as e:
        logger.warning(f"⚠️ Failed to pre-warm allowlist cache: {e}")
```

**C) Consider moving to database table:**
Instead of CSV in Blob Storage, store allowlist in PostgreSQL:
- Faster queries (indexed lookups)
- Better caching (database connection pool)
- Easier updates (no CSV parsing)

**Expected Improvement:** 50-80% reduction in allowlist check latency

---

### 4. 🟡 **JWT Verification on Every Request**

**Severity:** MEDIUM-HIGH  
**Impact:** Network calls to Azure AD on cold cache  
**Location:** `backend/utils/jwt_verification.py:32-99`, `backend/utils/dependencies.py:86-122`

#### Problem

Every authenticated request calls JWT verification, which includes:

**JWT Verification Flow:**
1. Extract JWT token from `Authorization` header
2. Fetch signing keys from Azure AD JWKS endpoint (if not cached)
3. Verify token signature
4. Validate claims (issuer, audience, expiration)

**Network Calls:**
```python
# In jwt_verification.py
signing_key = self.jwks_client.get_signing_key_from_jwt(token)  # May call Azure AD
```

**PyJWKClient caching:**
```python
self.jwks_client = PyJWKClient(
    jwks_url,
    cache_keys=True,  # Keys are cached
    max_cached_keys=16
)
```

**Issue:**
- When cache is cold or keys rotate, this calls Azure AD
- Azure AD JWKS endpoint: **100-500ms latency**
- In strict mode, failures block the request

#### Current Behavior

From `dependencies.py:86-122`:
```python
if authorization and authorization.startswith("Bearer "):
    jwt_token = authorization[7:]
    decoded_jwt = await jwt_verification_service.verify_jwt_token(jwt_token)
    # Cross-validates with Easy Auth
```

This happens on EVERY request to endpoints using `get_current_user()` or `get_allowlisted_user()`.

#### Solution

**Option A: Make JWT verification optional in production**
```python
# In settings
JWT_VERIFICATION_STRICT = False  # Only verify in dev/staging
```

Rationale: Azure Easy Auth already validates the token. JWT verification is defense-in-depth but adds latency.

**Option B: Cache decoded tokens temporarily**
```python
from functools import lru_cache
import hashlib

@lru_cache(maxsize=1000)
def get_cached_jwt_validation(token_hash: str, expiry: int):
    """Cache JWT validation results until token expires"""
    return True  # Or decoded claims

# In verify_jwt_token():
token_hash = hashlib.sha256(token.encode()).hexdigest()
expiry = decoded_token.get('exp')
```

**Expected Improvement:** 50-200ms reduction per request with cold JWT cache

---

### 5. 🟢 **`get_user_by_id()` Called Multiple Times**

**Severity:** MEDIUM  
**Impact:** Redundant database queries  
**Location:** `backend/api/routes.py:502-534`

#### Problem

Several endpoints call `get_user_by_id()` even though they already have the user from the dependency:

```python
@router.get("/users/me", response_model=User)
async def get_current_user_me_route(
    current_user: User = Depends(get_current_user),  # Already fetched user
):
    return get_user_by_id(current_user.id)  # ❌ Redundant query!
```

**Redundant queries in:**
- `/users/me` (line 511-516)
- `/user/profile` (line 519-524)
- `/user` (line 502-507)

#### Solution

Return the user directly from the dependency:

```python
@router.get("/users/me", response_model=User)
async def get_current_user_me_route(
    current_user: User = Depends(get_current_user),
):
    return current_user  # ✅ No extra query
```

**Expected Improvement:** 1 fewer database query per request (10-50ms)

---

## 6. 🟢 **Missing Query Timeout Configuration**

**Severity:** LOW-MEDIUM  
**Impact:** Slow queries can block connections  
**Location:** `backend/app/database/postgres_database.py:27-35`

#### Problem

The database engine has connection pooling but no query timeout:

```python
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=30,
    pool_timeout=30,  # Connection checkout timeout
    # No query timeout! ❌
)
```

**Risk:**
- Slow queries (missing indexes, bad query plans) hold connections
- Connection pool exhaustion
- Cascading failures

#### Solution

Add query timeout via connection options:

```python
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=30,
    pool_timeout=30,
    pool_recycle=3600,
    pool_pre_ping=True,
    connect_args={
        "options": "-c statement_timeout=30000"  # 30 second timeout
    }
)
```

**Expected Improvement:** Prevent slow queries from blocking the pool

---

## Performance Optimization Priority Matrix

| Issue | Severity | Effort | Impact | Priority |
|-------|----------|--------|--------|----------|
| N+1 Query Problem | CRITICAL | Low | Very High | 🔴 P0 |
| Missing Indexes | CRITICAL | Low | Very High | 🔴 P0 |
| Allowlist Caching | HIGH | Medium | High | 🟡 P1 |
| JWT Verification | MEDIUM | Low | Medium | 🟡 P1 |
| Redundant Queries | MEDIUM | Low | Low | 🟢 P2 |
| Query Timeouts | LOW | Low | Medium | 🟢 P2 |

---

## Implementation Checklist

### Phase 1: Critical Fixes (P0) - Deploy ASAP

- [ ] **Add database indexes**
  - [ ] Create migration for foreign key indexes
  - [ ] Test migration in dev/preprod
  - [ ] Deploy to production
  
- [ ] **Fix N+1 query in `fetch_transcriptions_metadata()`**
  - [ ] Add `selectinload()` for relationships
  - [ ] Test with users having many transcriptions
  - [ ] Verify query count reduction (use SQLAlchemy logging)

### Phase 2: High-Priority Optimizations (P1)

- [ ] **Optimize allowlist caching**
  - [ ] Increase cache TTL to 30 minutes
  - [ ] Add cache warmup on startup
  - [ ] Consider moving to database table
  
- [ ] **Optimize JWT verification**
  - [ ] Make strict mode configurable per environment
  - [ ] Add token caching layer
  - [ ] Monitor Azure AD call frequency

### Phase 3: Nice-to-Have Improvements (P2)

- [ ] **Remove redundant queries**
  - [ ] Refactor `/users/me` endpoint
  - [ ] Refactor `/user/profile` endpoint
  
- [ ] **Add query timeouts**
  - [ ] Configure statement timeout
  - [ ] Add query monitoring

---

## Expected Performance Improvements

### Before Optimizations

**P95 latency:** 15-20 seconds  
**P99 latency:** 20+ seconds

**Breakdown (estimated):**
- N+1 queries: 10-15 seconds (50+ transcriptions)
- Missing indexes: 3-5 seconds
- Allowlist check: 0.5-1 second (cold cache)
- JWT verification: 0.2-0.5 seconds (cold cache)
- Other: 0.3-1 second

### After Phase 1 (P0 Fixes)

**Expected P95 latency:** 0.5-1 second ⚡ (15-20x improvement)  
**Expected P99 latency:** 1-2 seconds ⚡ (10-20x improvement)

**Breakdown:**
- N+1 queries: 0.1-0.2 seconds (3 queries with eager loading)
- Missing indexes: 0.05-0.1 seconds (indexed lookups)
- Allowlist check: 0.5-1 second (cached)
- JWT verification: 0.1-0.2 seconds (cached)
- Other: 0.3-0.5 second

### After All Phases

**Expected P95 latency:** 0.2-0.5 seconds ⚡⚡  
**Expected P99 latency:** 0.5-1 second ⚡⚡

---

## Monitoring Recommendations

### Add Metrics to Track

1. **Database Query Metrics**
   ```python
   # Log query count and duration per request
   from sqlalchemy import event
   
   @event.listens_for(engine, "before_cursor_execute")
   def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
       # Track query count
       pass
   ```

2. **Allowlist Cache Hit Rate**
   ```python
   cache_hits = 0
   cache_misses = 0
   # Log hit rate every 1000 requests
   ```

3. **JWT Verification Duration**
   ```python
   # Add timing metrics to jwt_verification_service
   import time
   start = time.perf_counter()
   result = await verify_jwt_token(token)
   duration = time.perf_counter() - start
   logger.info(f"JWT verification took {duration*1000:.2f}ms")
   ```

### Application Insights Queries

```kusto
// Track endpoint latency trends
requests
| where timestamp > ago(1h)
| where url contains "/users/me" or url contains "/transcriptions-metadata"
| summarize 
    p50=percentile(duration, 50),
    p95=percentile(duration, 95),
    p99=percentile(duration, 99)
    by url, bin(timestamp, 5m)
| render timechart
```

---

## Additional Investigations Needed

1. **Database Connection Pool Exhaustion**
   - Monitor `pool_size` and `overflow` utilization
   - Check for connection leaks
   - Review `pool_timeout` errors in logs

2. **Azure Database Performance Tier**
   - Verify GP_Standard_D2s_v3 tier is sufficient
   - Check CPU, memory, and IOPS metrics
   - Consider upgrading if constrained

3. **Network Latency**
   - Measure latency between backend and Azure Database
   - Measure latency to Azure Blob Storage
   - Check if Azure regions are co-located

4. **SQLModel Relationship Configuration**
   - Review all `Relationship()` definitions
   - Consider adding `lazy="selectin"` or `lazy="joined"` globally

---

## Code Examples for Implementation

### 1. Database Index Migration

Create: `backend/alembic/versions/add_foreign_key_indexes.py`

```python
"""Add foreign key indexes for performance

Revision ID: <generated>
Revises: <previous_revision>
Create Date: 2025-11-05 00:00:00.000000
"""
from alembic import op

revision = '<generated>'
down_revision = '<previous_revision>'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add indexes for foreign keys to improve query performance
    op.create_index('ix_transcription_user_id', 'transcription', ['user_id'])
    op.create_index('ix_minuteversion_transcription_id', 'minuteversion', ['transcription_id'])
    op.create_index('ix_transcriptionjob_transcription_id', 'transcriptionjob', ['transcription_id'])

def downgrade() -> None:
    op.drop_index('ix_transcriptionjob_transcription_id', table_name='transcriptionjob')
    op.drop_index('ix_minuteversion_transcription_id', table_name='minuteversion')
    op.drop_index('ix_transcription_user_id', table_name='transcription')
```

### 2. Fix N+1 Query with Eager Loading

Update: `backend/app/database/interface_functions.py`

```python
from sqlalchemy.orm import selectinload

def fetch_transcriptions_metadata(user_id: UUID, tz) -> list[TranscriptionMetadata]:
    with Session(engine) as session:
        # Use eager loading to fetch relationships in batch
        statement = (
            select(Transcription)
            .where(Transcription.user_id == user_id)
            .options(
                selectinload(Transcription.minute_versions),
                selectinload(Transcription.transcription_jobs)
            )
        )
        transcriptions = session.exec(statement).all()
        
        current_time = datetime.now(UTC)
        
        return [
            TranscriptionMetadata(
                id=t.id,
                title=t.title or "",
                created_datetime=pytz.utc.localize(t.created_datetime).astimezone(tz),
                updated_datetime=(
                    pytz.utc.localize(t.updated_datetime).astimezone(tz)
                    if t.updated_datetime
                    else None
                ),
                is_showable_in_ui=_is_transcription_showable(t, current_time),
                speakers=_extract_unique_speakers(t),
            )
            for t in transcriptions
        ]
```

### 3. Increase Allowlist Cache TTL

Update: `backend/utils/dependencies.py`

```python
# Change cache TTL from 5 minutes to 30 minutes
allowlist_cache = get_allowlist_cache(ttl_seconds=1800)  # Was 300
```

### 4. Remove Redundant Queries

Update: `backend/api/routes.py`

```python
@router.get("/users/me", response_model=User)
async def get_current_user_me_route(
    current_user: User = Depends(get_current_user),
):
    """Get the current user's details (auth only, no allowlist check)."""
    # Return user directly from dependency - no extra query needed
    return current_user  # Changed from: get_user_by_id(current_user.id)

@router.get("/user/profile", response_model=User)
async def get_user_profile_route(
    current_user: User = Depends(get_current_user),
):
    """Get the current user's profile (auth only, no allowlist check)."""
    # Return user directly from dependency - no extra query needed
    return current_user  # Changed from: get_user_by_id(current_user.id)

@router.get("/user", response_model=User)
async def get_current_user_route(
    current_user: User = Depends(get_current_user),
):
    """Get the current user's details (auth only, no allowlist check)."""
    # Return user directly from dependency - no extra query needed
    return current_user  # Changed from: get_user_by_id(current_user.id)
```

---

## Testing Strategy

### 1. Load Testing

Use `locust` or `k6` to simulate production traffic:

```python
# locustfile.py
from locust import HttpUser, task, between

class APIUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def get_transcriptions_metadata(self):
        self.client.get("/transcriptions-metadata", 
                       headers={"Authorization": f"Bearer {self.token}"})
    
    @task(1)
    def get_user_me(self):
        self.client.get("/users/me",
                       headers={"Authorization": f"Bearer {self.token}"})
```

Run: `locust -f locustfile.py --host=https://your-api.azurewebsites.net`

### 2. Database Query Analysis

Enable SQLAlchemy query logging:

```python
# In postgres_database.py
engine = create_engine(
    DATABASE_URL,
    echo=True,  # Log all queries
    # ... other settings
)
```

Count queries per request and verify reduction.

### 3. APM Monitoring

Use Application Insights to track:
- Request duration (p50, p95, p99)
- Database query count per request
- External dependency calls (Azure AD, Blob Storage)
- Error rates

---

## Conclusion

The **20-second p95/p99 latencies** are caused by a combination of:
1. **N+1 query problem** (major contributor)
2. **Missing database indexes** (major contributor)
3. **Slow allowlist checks** (moderate contributor)
4. **JWT verification overhead** (minor contributor)

**Immediate action required:**
- Create and deploy database index migration
- Fix N+1 query with eager loading

**Expected outcome:**
- **P95 latency: 20s → 0.5s** (40x improvement)
- **P99 latency: 20s → 1s** (20x improvement)

These are straightforward fixes with minimal risk and massive performance gains. 🚀
