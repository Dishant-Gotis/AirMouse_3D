---
skill_name: aws-cdk-constructs
description: CDK constructs L1/L2/L3 patterns, CDK Pipelines, escape hatches, testing
category: Cloud & DevOps
version: 1.0.0
---

# AWS CDK Constructs

## Construct Levels: L1, L2, L3

**L1 (CloudFormation)**: Direct mapping to CloudFormation resources. Low-level but complete control.

```python
from aws_cdk import aws_s3 as s3
from aws_cdk import core

# L1 construct (CfnBucket)
bucket = s3.CfnBucket(
    self, 'RawBucket',
    bucket_name='my-raw-bucket',
    versioning_configuration=s3.CfnBucket.VersioningConfigurationProperty(
        status='Enabled'
    )
)
```

**L2 (AWS Constructs)**: Higher-level, opinionated, sensible defaults. Most commonly used.

```python
# L2 construct (Bucket)
bucket = s3.Bucket(
    self, 'DataBucket',
    block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
    versioning=True,
    encryption=s3.BucketEncryption.S3_MANAGED,
    enforce_ssl=True,
)
```

**L3 (Custom Components)**: Encapsulate multi-resource patterns for reuse.

```python
# Custom L3 construct
class DataLakeStack(core.Stack):
    def __init__(self, scope: core.Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # Raw data bucket
        self.raw_bucket = s3.Bucket(
            self, 'RawBucket',
            versioning=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
        )

        # Processed data bucket
        self.processed_bucket = s3.Bucket(
            self, 'ProcessedBucket',
            versioning=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
        )

        # Analysis bucket
        self.analysis_bucket = s3.Bucket(
            self, 'AnalysisBucket',
            public_read_access=False,
        )
```

## Custom Constructs (Reusable Components)

Create abstractions for common infrastructure patterns.

```python
from aws_cdk import aws_ec2 as ec2, aws_ecs as ecs, aws_elasticache as elasticache
from aws_cdk import core

class MicroserviceStack(core.Stack):
    """Full microservice with database, cache, and service discovery."""

    def __init__(self, scope: core.Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # VPC
        vpc = ec2.Vpc(self, 'VPC', max_azs=3)

        # Database
        db_instance = rds.DatabaseInstance(
            self, 'Database',
            engine=rds.DatabaseInstanceEngine.postgres(
                version=rds.PostgresEngineVersion.VER_13
            ),
            vpc=vpc,
            allocated_storage=100,
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.MEDIUM
            ),
        )

        # ElastiCache
        cache = elasticache.CfnCacheCluster(
            self, 'Cache',
            engine='redis',
            cache_node_type='cache.t3.micro',
            num_cache_nodes=1,
            vpc_security_group_ids=[
                vpc.default_security_group.security_group_id
            ],
        )

        # ECS Cluster
        cluster = ecs.Cluster(self, 'Cluster', vpc=vpc)

        self.vpc = vpc
        self.database = db_instance
        self.cache = cache
        self.cluster = cluster
```

## Testing Constructs

Validate construct behavior and CloudFormation output.

```python
import json
from aws_cdk import core, assertions
from aws_cdk import aws_s3 as s3

def test_bucket_encryption():
    """Test bucket has encryption enabled."""
    app = core.App()
    stack = core.Stack(app, 'TestStack')

    bucket = s3.Bucket(
        stack, 'TestBucket',
        encryption=s3.BucketEncryption.S3_MANAGED,
    )

    template = assertions.Template.from_stack(stack)

    # Assert bucket exists with encryption
    template.has_resource_properties(
        'AWS::S3::Bucket',
        {
            'BucketEncryption': {
                'ServerSideEncryptionConfiguration': [
                    {
                        'ServerSideEncryptionByDefault': {
                            'SSEAlgorithm': 'AES256'
                        }
                    }
                ]
            }
        }
    )

def test_security_group_rules():
    """Test security group has correct rules."""
    app = core.App()
    stack = core.Stack(app, 'TestStack')
    vpc = ec2.Vpc(stack, 'VPC')

    sg = ec2.SecurityGroup(
        stack, 'SecurityGroup',
        vpc=vpc,
        allow_all_outbound=False,
    )
    sg.add_ingress_rule(
        ec2.Peer.ipv4('10.0.0.0/8'),
        ec2.Port.tcp(443),
    )

    template = assertions.Template.from_stack(stack)
    template.resource_count_is('AWS::EC2::SecurityGroup', 1)
    template.assert_outputs(
        {
            'SecurityGroupId': assertions.Match.any_value()
        }
    )
```

## Escape Hatches

When CDK constructs don't support a feature, use escape hatches to access underlying resources.

```python
from aws_cdk import aws_lambda as lambda_
from aws_cdk import core

stack = core.Stack()

fn = lambda_.Function(
    stack, 'MyFunction',
    runtime=lambda_.Runtime.PYTHON_3_9,
    handler='index.handler',
    code=lambda_.Code.from_asset('lambda'),
)

# Access the underlying CloudFormation resource
cfn_fn = fn.node.default_child
cfn_fn.add_property_override(
    'Layers',
    ['arn:aws:lambda:us-east-1:123456789012:layer:MyLayer:1']
)

# Add custom JSON property
cfn_fn.add_metadata(
    'aws:cdk:disable-path-metadata',
    True
)
```

## CDK Pipelines for Continuous Deployment

Orchestrate multi-stack deployments with automated testing.

```python
from aws_cdk import aws_codepipeline as codepipeline
from aws_cdk import aws_codebuild as codebuild
from aws_cdk import pipelines, core

class PipelineStack(core.Stack):
    def __init__(self, scope: core.Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # Source code connection
        source_output = codepipeline.Artifact()
        source_action = pipelines.CodePipelineSource.github(
            repo='my-org/my-repo',
            branch='main',
            authentication=core.SecretValue.secrets_manager('github-token'),
        )

        # Synth step
        synth_step = pipelines.ShellStep(
            'Synth',
            input=source_action,
            commands=[
                'npm install -g aws-cdk',
                'npm ci',
                'npm run build',
                'npx cdk synth',
            ],
            primary_output_directory='cdk.out',
        )

        # Pipeline
        pipeline = pipelines.CodePipeline(
            self, 'Pipeline',
            synth=synth_step,
            self_mutation=True,
        )

        # Add stages
        dev_stage = pipeline.add_stage(DevStage(self, 'Dev'))
        prod_stage = pipeline.add_stage(
            ProdStage(self, 'Prod'),
            pre=[
                pipelines.ManualApprovalStep('ApprovalForProd'),
            ]
        )
```

## Configuration and Environments

Manage environment-specific values across stacks.

```python
from aws_cdk import core

class Config:
    def __init__(self, env: str):
        self.env = env
        self.configs = {
            'dev': {
                'instance_type': 't3.micro',
                'db_allocated_storage': 20,
                'db_engine_version': '13.7',
            },
            'prod': {
                'instance_type': 't3.large',
                'db_allocated_storage': 100,
                'db_engine_version': '13.7',
            },
        }

    def get(self, key: str):
        return self.configs[self.env].get(key)

# Usage
config = Config('prod')
instance_type = config.get('instance_type')  # 't3.large'
```

## Assets and Bundling

Package code and assets into CloudFormation stacks.

```python
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_s3_assets as s3_assets
from aws_cdk import core

stack = core.Stack()

# Lambda with source code bundled
fn = lambda_.Function(
    stack, 'MyFunction',
    runtime=lambda_.Runtime.PYTHON_3_9,
    handler='index.handler',
    code=lambda_.Code.from_asset(
        'lambda',
        bundling=core.BundlingOptions(
            image=core.DockerImage.from_registry('public.ecr.aws/lambda/python:3.9'),
            command=['bash', '-c', 'pip install -r requirements.txt -t /asset-output && cp -r . /asset-output'],
        )
    ),
)

# S3 asset
asset = s3_assets.Asset(
    stack, 'Asset',
    path='./data',
)
```

## Context and Feature Flags

Use context values for conditional logic and feature flags.

```python
from aws_cdk import core

stack = core.Stack()

# Context value
use_nat = stack.node.try_get_context('use-nat')

vpc = ec2.Vpc(
    stack, 'VPC',
    nat_gateways=1 if use_nat else 0,
)

# Use feature flag
use_new_naming = stack.node.try_get_context('new-naming-convention')
bucket_name = 'app-bucket-v2' if use_new_naming else 'app-bucket'
```

Pass context via cdk.json or CLI:

```bash
cdk deploy -c use-nat=true -c new-naming-convention=true
```
