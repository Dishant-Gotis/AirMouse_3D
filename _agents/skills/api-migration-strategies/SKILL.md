---
skill_name: API Migration Strategies
description: Plan and execute API migrations with versioning, deprecation periods, parallel running, and client communication
category: API & Integration
version: 1.0.0
---

# API Migration Strategies

## Overview
API evolution is inevitable. Master migration strategies for seamless transitions without breaking client applications.

## Versioning Strategy

```python
from flask import Flask, request, jsonify

app = Flask(__name__)

# URL-based versioning
@app.route('/api/v1/users/<user_id>', methods=['GET'])
def get_user_v1(user_id):
    user = User.query.get(user_id)
    return jsonify({
        'id': user.id,
        'name': user.name,
        'email': user.email
    })

@app.route('/api/v2/users/<user_id>', methods=['GET'])
def get_user_v2(user_id):
    user = User.query.get(user_id)
    return jsonify({
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'profile_url': f'/api/v2/users/{user.id}/profile'
    })

# Header-based versioning
@app.route('/api/users/<user_id>', methods=['GET'])
def get_user(user_id):
    version = request.headers.get('Accept-Version', '1')

    if version == '2':
        return get_user_v2(user_id)
    return get_user_v1(user_id)

# Determine version from header or URL
def get_api_version():
    version = request.headers.get('X-API-Version')
    if not version:
        # Extract from URL path
        parts = request.path.split('/')
        for i, part in enumerate(parts):
            if part.startswith('v'):
                version = part[1:]
                break

    return int(version) if version else 1
```

## Deprecation Timeline

```python
import warnings
from datetime import datetime

DEPRECATION_DATES = {
    'v1': {
        'deprecated_at': datetime(2024, 1, 1),
        'sunset_date': datetime(2025, 1, 1),
        'message': 'API v1 is deprecated. Please migrate to v2.',
        'migration_guide': 'https://docs.example.com/migration-v1-to-v2'
    }
}

def check_deprecation():
    version = get_api_version()
    version_key = f'v{version}'

    if version_key in DEPRECATION_DATES:
        deprecation_info = DEPRECATION_DATES[version_key]
        sunset = deprecation_info['sunset_date']

        # Add deprecation headers
        response = make_response()
        response.headers['Deprecation'] = 'true'
        response.headers['Sunset'] = sunset.isoformat()
        response.headers['Link'] = f'<{deprecation_info["migration_guide"]}>; rel="deprecation"'

        # Warn if past sunset
        if datetime.utcnow() > sunset:
            response.status_code = 410  # Gone
            response.data = jsonify({
                'error': 'API_DEPRECATED',
                'message': f'API {version_key} is no longer supported'
            })

        return response

    return None
```

## Parallel Running

```python
class ABTestRouter:
    def __init__(self, redis_client):
        self.redis = redis_client

    def route_request(self, user_id, endpoint):
        # Determine which version user gets
        bucket = self.redis.get(f"ab_test:{user_id}")

        if not bucket:
            # Assign randomly
            bucket = 'v2' if random.random() > 0.1 else 'v1'  # 10% to v1, 90% to v2
            self.redis.setex(f"ab_test:{user_id}", 86400*30, bucket)

        return bucket

    def compare_responses(self, endpoint, **kwargs):
        """Compare v1 and v2 responses for quality assurance"""
        v1_response = call_v1_endpoint(endpoint, **kwargs)
        v2_response = call_v2_endpoint(endpoint, **kwargs)

        # Compare
        differences = {
            'status_codes_match': v1_response['status'] == v2_response['status'],
            'data_equivalent': self._data_equivalent(v1_response['data'], v2_response['data'])
        }

        # Log for monitoring
        logger.info(f"Version comparison: {differences}")

        return differences

    def _data_equivalent(self, v1_data, v2_data):
        # Check if responses are semantically equivalent
        # Account for structural differences
        return True  # Implement comparison logic
```

## Client Communication

```python
# Deprecation notice email template
DEPRECATION_EMAIL = """
Subject: Action Required: API {old_version} Deprecation

Dear Developer,

We're writing to inform you that API {old_version} will be sunset on {sunset_date}.

**Current Status:**
- Deprecated: {deprecated_date}
- Final sunset: {sunset_date}

**Migration Guide:**
{migration_guide_url}

**What to do:**
1. Review the migration guide
2. Update your integration to use {new_version}
3. Test thoroughly in your sandbox environment
4. Deploy updates before the sunset date

**Questions?**
Contact our support team: api-support@example.com

Best regards,
The API Team
"""

def send_deprecation_notices():
    """Send deprecation notices to API users"""
    deprecated_apis = [
        v for v, info in DEPRECATION_DATES.items()
        if datetime.utcnow() > info['deprecated_at']
    ]

    for api in deprecated_apis:
        # Find users still using old API
        users = User.query.filter_by(api_version=api).all()

        for user in users:
            send_email(
                user.email,
                DEPRECATION_EMAIL.format(
                    old_version=api,
                    new_version=api.replace('v1', 'v2'),
                    deprecated_date=DEPRECATION_DATES[api]['deprecated_at'].date(),
                    sunset_date=DEPRECATION_DATES[api]['sunset_date'].date(),
                    migration_guide_url=DEPRECATION_DATES[api]['migration_guide']
                )
            )
```

## Monitoring Migration

```python
class MigrationMonitor:
    def __init__(self, redis_client):
        self.redis = redis_client

    def track_request(self, api_version, endpoint, response_time, status_code):
        date = datetime.utcnow().strftime('%Y-%m-%d')

        # Track by version
        self.redis.hincrby(
            f'api_metrics:{date}',
            f'v{api_version}:requests',
            1
        )

        # Track errors
        if status_code >= 400:
            self.redis.hincrby(
                f'api_metrics:{date}',
                f'v{api_version}:errors',
                1
            )

        # Track response time
        self.redis.lpush(
            f'response_times:{date}:v{api_version}',
            response_time
        )
        self.redis.ltrim(
            f'response_times:{date}:v{api_version}',
            0, 9999
        )

    def get_migration_progress(self):
        """Get percentage of users on each version"""
        dates = [
            (datetime.utcnow() - timedelta(days=i)).strftime('%Y-%m-%d')
            for i in range(30)
        ]

        progress = {}
        for date in dates:
            v1_reqs = int(self.redis.hget(f'api_metrics:{date}', 'v1:requests') or 0)
            v2_reqs = int(self.redis.hget(f'api_metrics:{date}', 'v2:requests') or 0)

            total = v1_reqs + v2_reqs
            if total > 0:
                progress[date] = {
                    'v1_percent': v1_reqs / total * 100,
                    'v2_percent': v2_reqs / total * 100
                }

        return progress
```

## Production Checklist

- [ ] Plan migration timeline (6-12 months recommended)
- [ ] Maintain both versions in parallel
- [ ] Send deprecation notices early
- [ ] Provide detailed migration guide
- [ ] Monitor version usage metrics
- [ ] Support gradual migration period
- [ ] Test thoroughly with real clients
- [ ] Have rollback plan ready
- [ ] Document all breaking changes
- [ ] Provide migration support channel
