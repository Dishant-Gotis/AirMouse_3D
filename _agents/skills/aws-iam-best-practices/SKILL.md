---
skill_name: AWS IAM Best Practices
description: Implement secure identity and access management with least privilege, roles, policies, SSO, and organization management
category: DevOps
version: 1.0.0
---

# AWS IAM Best Practices

## Overview
IAM is foundational to AWS security. Master role-based access control, policy design, and organizational governance to protect infrastructure.

## Least Privilege Architecture

### Policy Structure

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ReadEC2Only",
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeInstances",
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeTags"
      ],
      "Resource": "*"
    },
    {
      "Sid": "ModifyTagsOnlyInProd",
      "Effect": "Allow",
      "Action": "ec2:CreateTags",
      "Resource": "arn:aws:ec2:*:*:instance/*",
      "Condition": {
        "StringEquals": {
          "aws:RequestedRegion": "us-east-1"
        }
      }
    },
    {
      "Sid": "DenyHighRiskActions",
      "Effect": "Deny",
      "Action": [
        "iam:DeleteUser",
        "iam:DeleteRole",
        "iam:PutUserPolicy"
      ],
      "Resource": "*"
    }
  ]
}
```

### Role-Based Access

```python
import boto3
import json

iam = boto3.client('iam')

# Create role for EC2 instances
assume_role_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {"Service": "ec2.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }
    ]
}

role = iam.create_role(
    RoleName='ec2-application-role',
    AssumeRolePolicyDocument=json.dumps(assume_role_policy),
    Description='Application servers'
)

# Attach managed policy
iam.attach_role_policy(
    RoleName='ec2-application-role',
    PolicyArn='arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy'
)

# Create inline policy for specific resources
inline_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": ["s3:GetObject", "s3:PutObject"],
            "Resource": "arn:aws:s3:::app-data-bucket/*"
        }
    ]
}

iam.put_role_policy(
    RoleName='ec2-application-role',
    PolicyName='application-s3-access',
    PolicyDocument=json.dumps(inline_policy)
)

# Create instance profile and attach role
iam.create_instance_profile(InstanceProfileName='ec2-application')
iam.add_role_to_instance_profile(
    InstanceProfileName='ec2-application',
    RoleName='ec2-application-role'
)
```

## AWS Organizations & SCPs

### Organization Structure

```python
organizations = boto3.client('organizations')

# List accounts in organization
response = organizations.list_accounts()
for account in response['Accounts']:
    print(f"ID: {account['Id']}, Name: {account['Name']}, Status: {account['Status']}")

# Create OU for prod environment
root_id = organizations.list_roots()['Roots'][0]['Id']
prod_ou = organizations.create_organizational_unit(
    ParentId=root_id,
    Name='Production'
)

# Move account to OU
organizations.move_account(
    AccountId='123456789012',
    SourceParentId=root_id,
    DestinationParentId=prod_ou['OrganizationalUnit']['Id']
)
```

### Service Control Policies

```python
scp_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "DenyUnencryptedS3",
            "Effect": "Deny",
            "Action": "s3:PutObject",
            "Resource": "*",
            "Condition": {
                "StringNotEquals": {
                    "s3:x-amz-server-side-encryption": "AES256"
                }
            }
        },
        {
            "Sid": "DenyOldTLSVersions",
            "Effect": "Deny",
            "Action": "*",
            "Resource": "*",
            "Condition": {
                "NumericLessThan": {
                    "aws:SecureTransport": "1.2"
                }
            }
        }
    ]
}

organizations.create_policy(
    Content=json.dumps(scp_policy),
    Description='Security baseline for all accounts',
    Name='security-baseline',
    Type='SERVICE_CONTROL_POLICY'
)
```

## AWS SSO & Federation

### SSO Configuration

```python
sso = boto3.client('sso-admin')

# Create permission set
perm_set = sso.create_permission_set(
    InstanceArn='arn:aws:sso:::instance/ssoins-xxx',
    Name='AdminAccess',
    Description='Administrator access',
    SessionDuration='PT8H'  # 8 hours
)

# Attach AWS managed policy
sso.attach_managed_policy_to_permission_set(
    InstanceArn='arn:aws:sso:::instance/ssoins-xxx',
    PermissionSetArn=perm_set['PermissionSet']['PermissionSetArn'],
    ManagedPolicyArn='arn:aws:iam::aws:policy/AdministratorAccess'
)

# Assign to user
sso.create_account_assignment(
    InstanceArn='arn:aws:sso:::instance/ssoins-xxx',
    TargetId='123456789012',
    TargetType='AWS_ACCOUNT',
    PermissionSetArn=perm_set['PermissionSet']['PermissionSetArn'],
    PrincipalType='USER',
    PrincipalId='user-id-123'
)
```

### SAML/OIDC Federation

```python
# Create SAML provider
saml_metadata = """<EntityDescriptor>...</EntityDescriptor>"""

saml_provider = iam.create_saml_provider(
    SAMLMetadataDocument=saml_metadata,
    Name='okta-saml'
)

# Trust policy for federated user
trust_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Federated": saml_provider['SAMLProviderArn']
            },
            "Action": "sts:AssumeRoleWithSAML",
            "Condition": {
                "StringEquals": {
                    "SAML:aud": "https://signin.aws.amazon.com/saml"
                }
            }
        }
    ]
}

iam.create_role(
    RoleName='okta-federated-role',
    AssumeRolePolicyDocument=json.dumps(trust_policy)
)
```

## Cross-Account Access

```python
# Trust role in Account B for Account A
trust_policy_b = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::111111111111:role/account-a-role"
            },
            "Action": "sts:AssumeRole",
            "Condition": {
                "StringEquals": {
                    "sts:ExternalId": "unique-external-id-12345"
                }
            }
        }
    ]
}

# In Account B
iam.create_role(
    RoleName='cross-account-access',
    AssumeRolePolicyDocument=json.dumps(trust_policy_b)
)

# In Account A, allow assume role
assume_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "sts:AssumeRole",
            "Resource": "arn:aws:iam::222222222222:role/cross-account-access"
        }
    ]
}

iam.put_role_policy(
    RoleName='account-a-role',
    PolicyName='cross-account-assume',
    PolicyDocument=json.dumps(assume_policy)
)
```

## Access Analyzer & Auditing

```python
analyzer = boto3.client('accessanalyzer')

# Create analyzer
analyzer_response = analyzer.create_analyzer(
    analyzerName='org-analyzer',
    type='ORGANIZATION'
)

# Find public access
findings = analyzer.list_findings(
    analyzerArn=analyzer_response['arn'],
    filter={
        'resourceType': [{'eq': ['AWS::S3::Bucket']}],
        'isPublic': [{'eq': ['true']}]
    }
)

# Validate policy before deployment
validation = iam.simulate_custom_policy(
    PolicyInputList=[json.dumps(policy)],
    ActionNames=['s3:GetObject', 's3:PutObject'],
    ResourceArns=['arn:aws:s3:::my-bucket/*']
)
```

## Production Checklist

- [ ] Enable MFA for all users (not just console)
- [ ] Use roles instead of users for applications
- [ ] Implement least privilege from the start
- [ ] Enable CloudTrail for all IAM changes
- [ ] Use temporary credentials (STS) instead of long-lived keys
- [ ] Rotate access keys every 90 days
- [ ] Enable AWS SSO for centralized user management
- [ ] Use permission boundaries to limit maximum permissions
- [ ] Audit policies with Access Analyzer
- [ ] Enable organization-wide SCPs
