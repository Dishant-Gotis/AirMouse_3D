---
skill_name: aws-eks-kubernetes
description: EKS patterns for node groups, IRSA, cluster add-ons, Karpenter autoscaling, and Fargate profiles
category: Cloud & DevOps
version: 1.0.0
---

# AWS EKS (Elastic Kubernetes Service)

## Cluster Creation

### Create EKS Cluster
```bash
# Create IAM role for cluster
cluster_role=$(aws iam create-role \
  --role-name eks-cluster-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "eks.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }' \
  --query 'Role.Arn' \
  --output text)

# Attach EKS service policy
aws iam attach-role-policy \
  --role-name eks-cluster-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonEKSClusterPolicy

# Create cluster
aws eks create-cluster \
  --name prod-cluster \
  --version 1.28 \
  --role-arn $cluster_role \
  --resources-vpc-config subnetIds=subnet-12345,subnet-67890 \
  --logging enabledTypes=api,audit,authenticator,controllerManager,scheduler \
  --tags Environment=prod
```

### Get Cluster Credentials
```bash
# Update kubeconfig
aws eks update-kubeconfig \
  --region us-east-1 \
  --name prod-cluster

# Verify connectivity
kubectl get nodes
kubectl get pods -A
```

## Node Groups

### Managed Node Group
```bash
# Create node IAM role
node_role=$(aws iam create-role \
  --role-name eks-node-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "ec2.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }' \
  --query 'Role.Arn' \
  --output text)

# Attach required policies
aws iam attach-role-policy \
  --role-name eks-node-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy

aws iam attach-role-policy \
  --role-name eks-node-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy

aws iam attach-role-policy \
  --role-name eks-node-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly

# Create node group
aws eks create-nodegroup \
  --cluster-name prod-cluster \
  --nodegroup-name general-ng \
  --subnets subnet-12345 subnet-67890 \
  --node-role $node_role \
  --instance-types t3.medium t3.large \
  --desired-size 3 \
  --min-size 1 \
  --max-size 10 \
  --disk-size 50 \
  --tags Environment=prod
```

### Spot Instances for Cost Savings
```bash
aws eks create-nodegroup \
  --cluster-name prod-cluster \
  --nodegroup-name spot-ng \
  --subnets subnet-12345 subnet-67890 \
  --node-role $node_role \
  --instance-types t3.large t3.xlarge m5.large m5.xlarge \
  --desired-size 5 \
  --min-size 2 \
  --max-size 20 \
  --capacity-type SPOT  # 70% cheaper than on-demand
```

## IRSA (IAM Roles for Service Accounts)

Allow pods to assume IAM roles.

### Setup IRSA
```bash
# Get OIDC provider URL
oidc_id=$(aws eks describe-cluster \
  --name prod-cluster \
  --query 'cluster.identity.oidc.issuer' \
  --output text | cut -d'/' -f5)

oidc_provider="arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):oidc-provider/oidc.eks.us-east-1.amazonaws.com/id/$oidc_id"

# Create Kubernetes service account
kubectl create serviceaccount my-app -n default

# Create IAM role with trust policy
irsa_role=$(aws iam create-role \
  --role-name eks-my-app-role \
  --assume-role-policy-document "{
    \"Version\": \"2012-10-17\",
    \"Statement\": [{
      \"Effect\": \"Allow\",
      \"Principal\": {
        \"Federated\": \"$oidc_provider\"
      },
      \"Action\": \"sts:AssumeRoleWithWebIdentity\",
      \"Condition\": {
        \"StringEquals\": {
          \"oidc.eks.us-east-1.amazonaws.com/id/$oidc_id:sub\": \"system:serviceaccount:default:my-app\"
        }
      }
    }]
  }" \
  --query 'Role.Arn' \
  --output text)

# Attach policy
aws iam attach-role-policy \
  --role-name eks-my-app-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess

# Annotate Kubernetes service account
kubectl annotate serviceaccount my-app \
  -n default \
  eks.amazonaws.com/role-arn=$irsa_role
```

### Use IRSA in Pod
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-app
  namespace: default
spec:
  serviceAccountName: my-app
  containers:
  - name: app
    image: my-app:latest
    env:
    - name: AWS_ROLE_ARN
      value: arn:aws:iam::ACCOUNT:role/eks-my-app-role
    - name: AWS_WEB_IDENTITY_TOKEN_FILE
      value: /var/run/secrets/eks.amazonaws.com/serviceaccount/token
```

Pod now has access to S3 without storing credentials.

## Cluster Add-ons

### VPC CNI (Network Plugin)
```bash
aws eks create-addon \
  --cluster-name prod-cluster \
  --addon-name vpc-cni \
  --addon-version v1.14.1-eksbuild.1 \
  --service-account-role-arn $irsa_role
```

### CoreDNS
```bash
aws eks create-addon \
  --cluster-name prod-cluster \
  --addon-name coredns \
  --addon-version v1.9.3-eksbuild.2
```

### kube-proxy
```bash
aws eks create-addon \
  --cluster-name prod-cluster \
  --addon-name kube-proxy \
  --addon-version v1.28.1-eksbuild.1
```

## Karpenter Autoscaling

Advanced autoscaling that consolidates nodes and handles spot interruptions.

### Install Karpenter
```bash
# Create IAM role for Karpenter
karpenter_role=$(aws iam create-role \
  --role-name karpenter-controller-role \
  --assume-role-policy-document '{...}' \
  --query 'Role.Arn' \
  --output text)

# Install via Helm
helm repo add karpenter https://charts.karpenter.sh
helm install karpenter karpenter/karpenter \
  --namespace karpenter --create-namespace \
  --set serviceAccount.annotations."eks\.amazonaws\.com/role-arn"=$karpenter_role \
  --set settings.clusterName=prod-cluster
```

### Karpenter Provisioner
```yaml
apiVersion: karpenter.sh/v1alpha5
kind: Provisioner
metadata:
  name: default
spec:
  requirements:
  - key: kubernetes.io/arch
    operator: In
    values: ["amd64"]
  - key: karpenter.sh/capacity-type
    operator: In
    values: ["on-demand", "spot"]
  - key: node.kubernetes.io/instance-type
    operator: In
    values: ["t3.large", "t3.xlarge", "m5.large", "m5.xlarge"]
  providerRef:
    name: default
  limits:
    resources:
      cpu: 100
      memory: 100Gi
---
apiVersion: karpenter.k8s.aws/v1alpha1
kind: AWSNodeTemplate
metadata:
  name: default
spec:
  subnetSelector:
    karpenter.sh/discovery: "true"
  securityGroupSelector:
    karpenter.sh/discovery: "true"
```

Karpenter automatically:
- Adds nodes as pods need them
- Consolidates underutilized nodes
- Handles Spot interruptions gracefully

## Fargate Profiles

Serverless container execution (no node management).

```bash
# Create Fargate execution role
fargate_role=$(aws iam create-role \
  --role-name eks-fargate-pod-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "eks-fargate-pods.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }' \
  --query 'Role.Arn' \
  --output text)

aws iam attach-role-policy \
  --role-name eks-fargate-pod-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonEKSFargatePodExecutionRolePolicy

# Create Fargate profile
aws eks create-fargate-profile \
  --cluster-name prod-cluster \
  --fargate-profile-name fargate-profile \
  --pod-execution-role-arn $fargate_role \
  --subnets subnet-12345 subnet-67890 \
  --selectors namespace=fargate,labels=workload-type=batch
```

Deploy batch jobs to Fargate without managing nodes.

## Monitoring and Logging

### Container Insights
```bash
aws eks update-cluster-config \
  --name prod-cluster \
  --logging enabledTypes=api,audit,authenticator,controllerManager,scheduler

# Install CloudWatch Container Insights
helm repo add aws https://aws.github.io/eks-charts
helm install aws-cloudwatch-metrics aws/aws-cloudwatch-metrics \
  --namespace amazon-cloudwatch \
  --create-namespace
```

### Pod Monitoring
```bash
# View pod logs
kubectl logs pod-name -n namespace

# Stream logs
kubectl logs -f deployment/my-app -n default

# View resource usage
kubectl top nodes
kubectl top pods -A

# View events
kubectl get events -n default
```

## Best Practices

1. **Use managed node groups**: AWS handles patching and updates
2. **IRSA for pod credentials**: No static IAM keys in pods
3. **Karpenter for autoscaling**: Better consolidation than HPA alone
4. **Network policies**: Control pod-to-pod traffic
5. **RBAC**: Restrict user and service account access
6. **Pod security policies**: Enforce security standards
7. **Resource requests/limits**: Prevent resource starvation
8. **Multi-AZ**: Deploy across availability zones
9. **Monitoring**: CloudWatch Container Insights + Prometheus
10. **Secrets encryption**: Enable envelope encryption in EKS
