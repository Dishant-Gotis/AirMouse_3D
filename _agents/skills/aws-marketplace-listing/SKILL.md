---
skill_name: AWS Marketplace Listing
description: List products on AWS Marketplace with metering, contracts, support, and seller profile
category: Specialized Platform
version: 1.0.0
---

# AWS Marketplace Listing

## Product Types

```python
class AWSMarketplace:
    def product_types(self):
        return {
            'saas': 'Software as a service',
            'ami': 'Pre-configured machine images',
            'containers': 'Docker images',
            'professional_services': 'Consulting/implementation'
        }

    def listing_requirements(self):
        return {
            'product_information': 'Name, description, logo, category',
            'pricing': 'Hourly, monthly, annual, or usage-based',
            'support': 'Email, chat, phone contact info',
            'eula': 'End user license agreement',
            'iam_policy': 'Required permissions'
        }

    def metering(self):
        return {
            'dimensions': 'Units being charged (users, API calls)',
            'api': 'Submit usage records to AWS',
            'billing': 'AWS bills customer, pays you'
        }

    def contracts(self):
        return {
            'standalone': 'Customer purchases directly',
            'offer': 'Negotiated custom pricing',
            'renewal': 'Auto-renew or require resubscribe'
        }
```

## Production Checklist

- [ ] Prepare product information
- [ ] Create marketplace account
- [ ] Define pricing model
- [ ] Implement metering (if usage-based)
- [ ] Configure support channels
- [ ] Submit EULA
- [ ] Specify IAM permissions
- [ ] Test in AWS Marketplace
- [ ] Submit for review
- [ ] Monitor for issues
