---
skill_name: aws-cdk-patterns
description: AWS CDK patterns for constructs, stacks, aspects, testing with fine-grained assertions
category: Cloud & DevOps
version: 1.0.0
---

# AWS CDK Patterns

## CDK Basics

CDK allows infrastructure as code in Python, TypeScript, etc.

### Initialize CDK Project
```bash
npm install -g aws-cdk
cdk init app --language python

# Directory structure
# ├── app.py
# ├── cdk.json
# ├── requirements.txt
# └── stacks/
#     └── my_stack.py
```

### Basic Stack
```python
from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_s3 as s3,
    Duration
)
from constructs import Construct

class MyStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # Create VPC
        vpc = ec2.Vpc(self, "VPC",
            cidr="10.0.0.0/16",
            max_azs=2,
            nat_gateways=1
        )

        # Create S3 bucket
        bucket = s3.Bucket(self, "MyBucket",
            bucket_name="my-unique-bucket",
            versioned=True,
            block_public_access=s3.BlockPublicAccess(
                block_public_acls=True,
                block_public_policy=True,
                ignore_public_acls=True,
                restrict_public_buckets=True
            ),
            lifecycle_rules=[
                s3.LifecycleRule(
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.STANDARD_IA,
                            transition_after=Duration.days(30)
                        )
                    ]
                )
            ]
        )
```

## Constructs

Building blocks for AWS resources.

### L1 Constructs (CloudFormation)
Low-level, direct CloudFormation representation:

```python
# L1 construct (CfnBucket = CloudFormation Bucket)
bucket = s3.CfnBucket(self, "L1Bucket",
    bucket_name="my-bucket"
)
```

### L2 Constructs (Opinionated)
Higher-level, AWS-recommended patterns:

```python
# L2 construct (Bucket = CDK best practices)
bucket = s3.Bucket(self, "L2Bucket",
    bucket_name="my-bucket",
    versioned=True,
    block_public_access=s3.BlockPublicAccess.BLOCK_ALL
)
```

### L3 Constructs (Custom)
Multi-resource patterns you define:

```python
class WebServerStack(Construct):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # VPC
        vpc = ec2.Vpc(self, "VPC")

        # Security group
        sg = ec2.SecurityGroup(self, "SG",
            vpc=vpc,
            allow_all_outbound=True
        )
        sg.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(80)
        )

        # EC2 instance
        self.instance = ec2.Instance(self, "Instance",
            vpc=vpc,
            instance_type=ec2.InstanceType("t3.micro"),
            machine_image=ec2.AmazonLinuxImage(),
            security_group=sg
        )
```

## Stack Organization

Organize infrastructure into logical stacks.

### Multiple Stacks
```python
from aws_cdk import App

app = App()

# Database stack
db_stack = DatabaseStack(app, "db-stack",
    env=cdk.Environment(
        account="123456789012",
        region="us-east-1"
    )
)

# Compute stack
compute_stack = ComputeStack(app, "compute-stack",
    env=cdk.Environment(
        account="123456789012",
        region="us-east-1"
    )
)

# Network stack
network_stack = NetworkStack(app, "network-stack")

# Add dependencies
compute_stack.add_dependency(db_stack)
compute_stack.add_dependency(network_stack)

app.synth()
```

## Aspects

Apply changes to multiple constructs automatically.

### Custom Aspect
```python
from aws_cdk import core

class RequireMFADeletion(core.IAspect):
    def visit(self, node):
        if isinstance(node, s3.CfnBucket):
            node.versioning_configuration = s3.CfnBucket.VersioningConfigurationProperty(
                status="Enabled"
            )
            node.add_property_override("MfaDelete", True)

class TaggingAspect(core.IAspect):
    def __init__(self, environment: str):
        self.environment = environment

    def visit(self, node):
        core.Tags.of(node).add("Environment", self.environment)
        core.Tags.of(node).add("ManagedBy", "CDK")

# Apply aspect to stack
aspect = TaggingAspect("prod")
core.Aspects.of(stack).add(aspect)
```

## Testing

Validate CDK stacks programmatically.

### Fine-Grained Assertions
```python
import unittest
from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_lambda as lambda_,
)
from aws_cdk.assertions import Template, Match

class TestMyStack(unittest.TestCase):
    def test_bucket_exists(self):
        stack = Stack()
        s3.Bucket(stack, "MyBucket")

        template = Template.from_stack(stack)

        # Assert bucket exists
        template.resource_count_is("AWS::S3::Bucket", 1)

    def test_bucket_versioning_enabled(self):
        stack = Stack()
        s3.Bucket(stack, "MyBucket", versioned=True)

        template = Template.from_stack(stack)

        # Assert versioning is enabled
        template.has_resource_properties("AWS::S3::Bucket", {
            "VersioningConfiguration": {
                "Status": "Enabled"
            }
        })

    def test_lambda_environment_variables(self):
        stack = Stack()
        fn = lambda_.Function(stack, "MyFunction",
            code=lambda_.Code.from_asset("lambda"),
            handler="index.handler",
            runtime=lambda_.Runtime.PYTHON_3_9,
            environment={"DB_HOST": "localhost"}
        )

        template = Template.from_stack(stack)

        # Assert environment variables
        template.has_resource_properties("AWS::Lambda::Function", {
            "Environment": {
                "Variables": Match.object_like({"DB_HOST": "localhost"})
            }
        })

    def test_count_resources(self):
        stack = Stack()
        s3.Bucket(stack, "Bucket1")
        s3.Bucket(stack, "Bucket2")
        s3.Bucket(stack, "Bucket3")

        template = Template.from_stack(stack)
        template.resource_count_is("AWS::S3::Bucket", 3)

    def test_snapshot_matching(self):
        """Ensure CloudFormation template hasn't changed"""
        stack = Stack()
        s3.Bucket(stack, "MyBucket")

        template = Template.from_stack(stack)

        # First run: creates snapshot
        # Subsequent runs: compare to snapshot
        template.assert_matches_template({
            "Resources": Match.any()
        })

if __name__ == "__main__":
    unittest.main()
```

## Parameters and Configuration

Pass values to stacks.

```python
from aws_cdk import Stack
from constructs import Construct

class MyStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # Get context values
        environment = self.node.try_get_context("environment")
        availability_zones = self.node.try_get_context("azs")

        # Use in stack
        vpc = ec2.Vpc(self, "VPC",
            max_azs=len(availability_zones) if availability_zones else 2
        )
```

### Context Values
```json
// cdk.json
{
  "context": {
    "environment": "prod",
    "azs": ["us-east-1a", "us-east-1b", "us-east-1c"],
    "instance-type": "t3.large"
  }
}
```

Or pass via CLI:
```bash
cdk deploy -c environment=prod -c instance-type=t3.large
```

## Synthesizing and Deploying

```bash
# Generate CloudFormation template
cdk synth

# View generated CloudFormation
cat cdk.out/MyStack.template.json

# Deploy to AWS
cdk deploy

# Deploy with parameters
cdk deploy --require-approval never

# Deploy multiple stacks
cdk deploy Stack1 Stack2 --hotswap  # Faster for Lambda code changes

# Destroy resources
cdk destroy
```

## Best Practices

1. **Use L2 constructs**: Better defaults than L1
2. **Organize by stack**: Database, compute, network as separate stacks
3. **Reuse constructs**: Create custom L3 constructs for patterns
4. **Aspects for enforcement**: Apply tags, encryption automatically
5. **Test assertions**: Validate template structure
6. **Environment-specific config**: Use context or separate stacks
7. **Dependencies**: Explicit add_dependency between stacks
8. **Imports**: Reference resources from other stacks
9. **Escape hatches**: Use node.add_property_override for unsupported features
10. **Version control**: Commit synthesized templates
