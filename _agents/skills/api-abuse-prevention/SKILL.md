---
skill_name: api-abuse-prevention
description: API abuse prevention - bot detection, behavioral analysis, ML-based scoring, rate limiting
category: [security, advanced]
version: 1.0.0
---

# API Abuse Prevention

## Bot Detection Techniques

```python
class BotDetectionEngine:
    def analyze_request(self, request):
        """Classify request as human or bot"""
        features = {
            'user_agent': self.parse_user_agent(request.headers['user-agent']),
            'request_pattern': self.analyze_pattern(request),
            'behavioral': self.behavioral_analysis(request),
            'network': self.network_analysis(request),
            'browser': self.browser_fingerprint(request)
        }

        score = self.calculate_score(features)
        return {
            'score': score,  # 0-100 (0=human, 100=bot)
            'risk_level': 'low' if score < 30 else 'medium' if score < 70 else 'high',
            'evidence': features
        }

    def analyze_pattern(self, request):
        """Check for bot-like patterns"""
        patterns = {
            'rapid_requests': self.requests_per_minute > 100,
            'identical_parameters': len(set(request.params)) == 1,
            'systematic_enumeration': self.is_sequential_ids(),
            'no_user_interaction': not self.has_javascript_execution(),
            'missing_referer': not request.headers.get('referer'),
            'suspicious_user_agent': self.is_known_bot_ua(request.headers['user-agent'])
        }
        return sum(patterns.values())

    def behavioral_analysis(self, request):
        """Analyze user behavior"""
        user_history = self.get_user_history(request.user_id)

        deviations = {
            'unusual_time': not self.is_normal_time(request.timestamp),
            'unusual_location': not self.is_usual_location(request.ip),
            'new_device': request.device_fingerprint not in user_history['devices'],
            'bulk_action': self.action_count_this_minute > normal_baseline,
            'no_think_time': request.time_since_last_action < 0.5  # seconds
        }
        return sum(deviations.values())

    def browser_fingerprint(self, request):
        """Advanced browser fingerprinting"""
        fingerprint = {
            'canvas_fingerprint': request.canvas_hash,
            'webgl_fingerprint': request.webgl_info,
            'font_list': request.fonts,
            'screen_resolution': request.screen_size,
            'timezone': request.timezone,
            'language': request.accept_language,
            'plugins': request.plugins
        }

        # Check consistency with known fingerprints
        if self.is_new_fingerprint(fingerprint):
            return 20  # Low confidence, new device
        elif self.fingerprint_appears_synthetic(fingerprint):
            return 80  # High suspicion of headless/bot
        else:
            return 0  # Normal

    def calculate_score(self, features):
        """ML-based scoring"""
        weights = {
            'user_agent': 0.2,
            'request_pattern': 0.3,
            'behavioral': 0.25,
            'network': 0.15,
            'browser': 0.1
        }

        score = sum(
            features[key] * weights[key] / 100
            for key in features
        ) * 100

        return min(score, 100)
```

## Rate Limiting Strategies

```python
class RateLimiter:
    """Adaptive rate limiting based on bot score"""

    def __init__(self):
        self.redis = redis.Redis()

    def check_rate_limit(self, user_id, bot_score):
        """Determine if request should be rate-limited"""
        limits = {
            'human': 1000,  # requests per hour
            'suspicious': 100,
            'likely_bot': 10,
            'confirmed_bot': 1
        }

        if bot_score < 30:
            limit = limits['human']
        elif bot_score < 70:
            limit = limits['suspicious']
        elif bot_score < 90:
            limit = limits['likely_bot']
        else:
            limit = limits['confirmed_bot']

        key = f"rate_limit:{user_id}"
        current = self.redis.incr(key)
        self.redis.expire(key, 3600)

        if current > limit:
            return {
                'allowed': False,
                'remaining': 0,
                'reset_in': self.redis.ttl(key)
            }

        return {
            'allowed': True,
            'remaining': limit - current,
            'reset_in': self.redis.ttl(key)
        }

    def sliding_window(self, user_id, max_requests, window_seconds):
        """Sliding window rate limit"""
        key = f"window:{user_id}"
        now = time.time()
        window_start = now - window_seconds

        # Add current request
        self.redis.zadd(key, {str(now): now})

        # Remove old requests outside window
        self.redis.zremrangebyscore(key, 0, window_start)

        # Count requests in window
        count = self.redis.zcard(key)

        # Set expiry
        self.redis.expire(key, window_seconds)

        return count <= max_requests
```

## Behavioral Analysis

```python
class BehavioralAnalyzer:
    def get_user_baseline(self, user_id):
        """Establish normal behavior for user"""
        history = self.database.get_user_history(user_id, days=30)

        return {
            'avg_requests_per_hour': self.calculate_mean(history, 'requests/hour'),
            'std_dev': self.calculate_std_dev(history),
            'peak_hours': self.find_peak_hours(history),
            'common_endpoints': self.get_top_endpoints(history),
            'usual_locations': self.get_locations(history),
            'devices': self.get_devices(history)
        }

    def detect_anomalies(self, user_id, current_behavior):
        """Detect deviation from baseline"""
        baseline = self.get_user_baseline(user_id)

        anomalies = []

        # Request rate anomaly
        if current_behavior['request_rate'] > baseline['avg_requests_per_hour'] + (3 * baseline['std_dev']):
            anomalies.append({
                'type': 'request_rate',
                'severity': 'high',
                'message': f"Requests {3*baseline['std_dev']}x above normal"
            })

        # Location anomaly
        if current_behavior['location'] not in baseline['usual_locations']:
            # Check travel time feasibility
            if not self.is_feasible_travel(current_behavior['location']):
                anomalies.append({
                    'type': 'impossible_travel',
                    'severity': 'critical',
                    'message': f"Impossible travel time to {current_behavior['location']}"
                })

        # Device anomaly
        if current_behavior['device_id'] not in baseline['devices']:
            anomalies.append({
                'type': 'new_device',
                'severity': 'medium'
            })

        return anomalies
```

## Captcha & Challenge-Response

```javascript
class ChallengeSystem {
  async issueChallenge(userRequest, suspicionLevel) {
    const challenge = {
      id: generateId(),
      type: this.selectChallengeType(suspicionLevel),
      difficulty: this.calculateDifficulty(suspicionLevel),
      timestamp: Date.now(),
      expiresAt: Date.now() + 5 * 60 * 1000  // 5 minutes
    };

    switch (challenge.type) {
      case 'captcha':
        // Google reCAPTCHA v3 (invisible)
        // Returns score 0-1
        const captchaScore = await this.verifyCaptcha(userRequest);
        if (captchaScore < 0.5) {
          return { challenge_required: true, type: 'captcha' };
        }
        break;

      case 'proof_of_work':
        // Computational challenge (e.g., find hash with N leading zeros)
        return {
          challenge_required: true,
          nonce: challenge.id,
          difficulty: challenge.difficulty
        };

      case 'device_challenge':
        // Verify device ownership (push notification, SMS)
        await this.sendDeviceChallenge(userRequest.user_id);
        return { challenge_required: true, type: 'sms' };

      case 'behavioral':
        // Ask user to answer security questions
        const questions = this.getSecurityQuestions(userRequest.user_id, 3);
        return { challenge_required: true, type: 'questions', questions };
    }

    return { challenge_required: false };
  }

  selectChallengeType(suspicionLevel) {
    if (suspicionLevel < 0.3) return null;  // No challenge
    if (suspicionLevel < 0.6) return 'captcha';
    if (suspicionLevel < 0.8) return 'device_challenge';
    return 'behavioral';  // Multi-factor verification
  }
}
```

## Monitoring & Metrics

```
Bot Traffic Metrics:
- Bot detection rate: % of traffic identified as bot
- False positive rate: % of legitimate users blocked
- Traffic origin: % from known bot IPs/ASNs
- Attack volume: Requests/second from bots

Effectiveness:
- Brute force attempts blocked: Count
- Credential stuffing prevented: User accounts protected
- Scraping prevented: Data bandwidth saved
- API rate limit violations prevented: Count

ROI:
- Cost of infrastructure saved (fewer bots consuming resources)
- Cost of data breaches prevented
- Customer experience impact (false positives)
```

## Key Takeaways

- **Multi-layered**: UA, behavior, fingerprint, network analysis
- **Adaptive**: Limits based on risk level
- **Invisible**: Human users unaffected by detection
- **Continuous**: Update baselines and patterns
- **Challenge**: Deploy when suspicion is high
