---
skill_name: API Monetization Guide
description: Monetize APIs with pricing models, tier management, usage metering, billing integration, and developer portals
category: API & Integration
version: 1.0.0
---

# API Monetization Guide

## Overview
Monetizing APIs requires careful design of pricing, metering, and billing. Master strategies for sustainable API businesses.

## Pricing Models

```python
class PricingTier:
    TIERS = {
        'free': {
            'name': 'Free',
            'price': 0,
            'requests_per_month': 10000,
            'features': ['basic_endpoints']
        },
        'pro': {
            'name': 'Professional',
            'price': 99,
            'requests_per_month': 1000000,
            'features': ['all_endpoints', 'webhooks', 'priority_support']
        },
        'enterprise': {
            'name': 'Enterprise',
            'price': 'custom',
            'requests_per_month': float('inf'),
            'features': ['all_features', 'sso', 'sla', 'dedicated_support']
        }
    }

    @classmethod
    def get_tier(cls, tier_name):
        return cls.TIERS.get(tier_name)

    @classmethod
    def get_available_tiers(cls):
        return cls.TIERS

# Usage metering
class UsageMetrics:
    def __init__(self, api_key):
        self.api_key = api_key

    def get_tier(self):
        user = User.query.filter_by(api_key=api_key).first()
        return user.subscription_tier

    def record_request(self):
        tier = self.get_tier()
        limit = PricingTier.TIERS[tier]['requests_per_month']

        # Increment counter
        redis.incr(f"api_usage:{self.api_key}:{current_month}")
        redis.expire(f"api_usage:{self.api_key}:{current_month}", 30*24*60*60)

    def get_usage(self):
        usage = redis.get(f"api_usage:{self.api_key}:{current_month}") or 0
        tier = self.get_tier()
        limit = PricingTier.TIERS[tier]['requests_per_month']

        return {
            'used': int(usage),
            'limit': limit,
            'remaining': max(0, limit - int(usage)),
            'percent_used': int(usage) / limit * 100 if limit > 0 else 0
        }
```

## Metering & Billing

```python
from datetime import datetime, timedelta

class MeterRegistry:
    METERS = {
        'api_requests': 'Requests to API',
        'storage_gb': 'Storage used (GB)',
        'data_processed': 'Data processed (GB)',
        'custom_domains': 'Custom domains'
    }

    @classmethod
    def record_usage(cls, api_key, meter_name, quantity):
        if meter_name not in cls.METERS:
            raise ValueError(f"Unknown meter: {meter_name}")

        month = datetime.utcnow().strftime('%Y-%m')
        key = f"meter:{meter_name}:{api_key}:{month}"

        redis.incrbyfloat(key, quantity)
        redis.expire(key, 90*24*60*60)  # 90 days retention

    @classmethod
    def get_monthly_usage(cls, api_key, meter_name):
        month = datetime.utcnow().strftime('%Y-%m')
        key = f"meter:{meter_name}:{api_key}:{month}"
        return float(redis.get(key) or 0)

class BillingCalculator:
    PRICING = {
        'api_requests': 0.0001,  # $0.0001 per request
        'storage_gb': 0.10,      # $0.10 per GB/month
        'data_processed': 0.05,  # $0.05 per GB
        'custom_domains': 1.00   # $1.00 per domain/month
    }

    @classmethod
    def calculate_overage(cls, api_key, tier):
        tier_data = PricingTier.TIERS[tier]
        requests_limit = tier_data['requests_per_month']

        usage = MeterRegistry.get_monthly_usage(api_key, 'api_requests')
        overage = max(0, usage - requests_limit)

        return overage * cls.PRICING['api_requests']

    @classmethod
    def calculate_invoice(cls, api_key, month):
        tier = User.query.filter_by(api_key=api_key).first().subscription_tier
        subscription_price = PricingTier.TIERS[tier]['price']

        # Overage charges
        overage = cls.calculate_overage(api_key, tier)

        # Additional usage charges
        storage = MeterRegistry.get_monthly_usage(api_key, 'storage_gb')
        storage_charge = storage * cls.PRICING['storage_gb']

        data_processed = MeterRegistry.get_monthly_usage(api_key, 'data_processed')
        data_charge = data_processed * cls.PRICING['data_processed']

        domains = MeterRegistry.get_monthly_usage(api_key, 'custom_domains')
        domain_charge = domains * cls.PRICING['custom_domains']

        total = subscription_price + overage + storage_charge + data_charge + domain_charge

        return {
            'subscription': subscription_price,
            'overage_requests': overage,
            'storage': storage_charge,
            'data_processed': data_charge,
            'custom_domains': domain_charge,
            'total': total,
            'currency': 'USD'
        }
```

## Developer Portal

```python
from flask import Blueprint, render_template, request, jsonify

api_portal = Blueprint('portal', __name__, url_prefix='/portal')

@api_portal.route('/dashboard')
def dashboard():
    user = current_user
    usage = UsageMetrics(user.api_key).get_usage()
    invoice = BillingCalculator.calculate_invoice(user.api_key, current_month)

    return render_template('dashboard.html', {
        'usage': usage,
        'invoice': invoice,
        'tier': user.subscription_tier
    })

@api_portal.route('/api-keys', methods=['GET', 'POST'])
def api_keys():
    if request.method == 'POST':
        key = secrets.token_urlsafe(32)
        user = current_user
        user.api_keys.append(APIKey(key=key, name=request.json['name']))
        db.session.commit()
        return jsonify({'api_key': key}), 201

    return jsonify([k.to_dict() for k in current_user.api_keys])

@api_portal.route('/api-keys/<key_id>', methods=['DELETE'])
def delete_api_key(key_id):
    key = APIKey.query.filter_by(id=key_id, user_id=current_user.id).first()
    if not key:
        return jsonify({'error': 'Key not found'}), 404

    db.session.delete(key)
    db.session.commit()
    return '', 204

@api_portal.route('/usage', methods=['GET'])
def get_usage():
    api_key = request.args.get('api_key')
    metrics = UsageMetrics(api_key)
    return jsonify(metrics.get_usage())

@api_portal.route('/invoices', methods=['GET'])
def list_invoices():
    user = current_user
    invoices = Invoice.query.filter_by(user_id=user.id).order_by(Invoice.date.desc()).all()
    return jsonify([i.to_dict() for i in invoices])
```

## Integration with Stripe

```python
import stripe

stripe.api_key = "sk_live_..."

class StripeSubscriptionManager:
    @staticmethod
    def create_subscription(user, tier, payment_method_id):
        stripe_customer = stripe.Customer.create(
            email=user.email,
            name=user.name,
            payment_method=payment_method_id,
            invoice_settings={'default_payment_method': payment_method_id}
        )

        price_id = STRIPE_PRICE_IDS[tier]

        subscription = stripe.Subscription.create(
            customer=stripe_customer.id,
            items=[{'price': price_id}],
            expand=['latest_invoice.payment_intent']
        )

        user.stripe_customer_id = stripe_customer.id
        user.subscription_tier = tier
        db.session.commit()

        return subscription

    @staticmethod
    def handle_webhook(event):
        if event['type'] == 'invoice.payment_succeeded':
            invoice = event['data']['object']
            # Update user subscription status

        elif event['type'] == 'invoice.payment_failed':
            invoice = event['data']['object']
            # Send payment failure notice
```

## Production Checklist

- [ ] Design tiered pricing aligned with usage
- [ ] Implement usage metering for all resources
- [ ] Automate invoice generation
- [ ] Integrate with billing provider (Stripe, Zuora)
- [ ] Set up usage alerts
- [ ] Monitor metric accuracy
- [ ] Provide detailed usage analytics
- [ ] Implement fraud detection
- [ ] Support usage-based billing
- [ ] Document pricing clearly
