---
skill_name: aws-vpc-networking
description: VPC networking patterns for subnets, security groups, NACLs, transit gateways, VPC peering, and PrivateLink
category: Cloud & DevOps
version: 1.0.0
---

# AWS VPC Networking

## VPC Fundamentals

### Create VPC with CIDR Block
```bash
vpc_id=$(aws ec2 create-vpc \
  --cidr-block 10.0.0.0/16 \
  --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=prod-vpc}]' \
  --query 'Vpc.VpcId' \
  --output text)

# Enable DNS hostnames
aws ec2 modify-vpc-attribute \
  --vpc-id $vpc_id \
  --enable-dns-hostnames

# Enable DNS resolution
aws ec2 modify-vpc-attribute \
  --vpc-id $vpc_id \
  --enable-dns-support
```

### Subnets
```bash
# Public subnet (10.0.1.0/24)
pub_subnet=$(aws ec2 create-subnet \
  --vpc-id $vpc_id \
  --cidr-block 10.0.1.0/24 \
  --availability-zone us-east-1a \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=public-1a}]' \
  --query 'Subnet.SubnetId' \
  --output text)

# Private subnet (10.0.10.0/24)
priv_subnet=$(aws ec2 create-subnet \
  --vpc-id $vpc_id \
  --cidr-block 10.0.10.0/24 \
  --availability-zone us-east-1a \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=private-1a}]' \
  --query 'Subnet.SubnetId' \
  --output text)
```

## Internet Gateway and NAT

### Internet Gateway for Public Subnet
```bash
# Create and attach IGW
igw_id=$(aws ec2 create-internet-gateway \
  --tag-specifications 'ResourceType=internet-gateway,Tags=[{Key=Name,Value=prod-igw}]' \
  --query 'InternetGateway.InternetGatewayId' \
  --output text)

aws ec2 attach-internet-gateway \
  --vpc-id $vpc_id \
  --internet-gateway-id $igw_id

# Create public route table
pub_rt=$(aws ec2 create-route-table \
  --vpc-id $vpc_id \
  --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=public-rt}]' \
  --query 'RouteTable.RouteTableId' \
  --output text)

# Add route to IGW
aws ec2 create-route \
  --route-table-id $pub_rt \
  --destination-cidr-block 0.0.0.0/0 \
  --gateway-id $igw_id

# Associate route table with public subnet
aws ec2 associate-route-table \
  --subnet-id $pub_subnet \
  --route-table-id $pub_rt
```

### NAT Gateway for Private Subnet
```bash
# Allocate Elastic IP for NAT
eip=$(aws ec2 allocate-address \
  --domain vpc \
  --tag-specifications 'ResourceType=elastic-ip,Tags=[{Key=Name,Value=nat-eip}]' \
  --query 'AllocationId' \
  --output text)

# Create NAT Gateway in public subnet
nat_id=$(aws ec2 create-nat-gateway \
  --subnet-id $pub_subnet \
  --allocation-id $eip \
  --tag-specifications 'ResourceType=natgateway,Tags=[{Key=Name,Value=nat-gw}]' \
  --query 'NatGateway.NatGatewayId' \
  --output text)

# Wait for NAT to be available
aws ec2 wait nat-gateway-available --nat-gateway-ids $nat_id

# Create private route table
priv_rt=$(aws ec2 create-route-table \
  --vpc-id $vpc_id \
  --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=private-rt}]' \
  --query 'RouteTable.RouteTableId' \
  --output text)

# Add route to NAT Gateway
aws ec2 create-route \
  --route-table-id $priv_rt \
  --destination-cidr-block 0.0.0.0/0 \
  --nat-gateway-id $nat_id

# Associate with private subnet
aws ec2 associate-route-table \
  --subnet-id $priv_subnet \
  --route-table-id $priv_rt
```

## Security Groups

Control inbound/outbound traffic at instance level.

### Create Security Group
```bash
sg=$(aws ec2 create-security-group \
  --group-name web-sg \
  --description "Web server security group" \
  --vpc-id $vpc_id \
  --query 'GroupId' \
  --output text)

# Inbound: Allow HTTP/HTTPS from anywhere
aws ec2 authorize-security-group-ingress \
  --group-id $sg \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
  --group-id $sg \
  --protocol tcp \
  --port 443 \
  --cidr 0.0.0.0/0

# Inbound: Allow SSH from admin network
aws ec2 authorize-security-group-ingress \
  --group-id $sg \
  --protocol tcp \
  --port 22 \
  --cidr 203.0.113.0/24

# Outbound: Allow all (default)
# No action needed — VPC security groups allow all outbound by default
```

### Security Group Chaining
```bash
# DB security group
db_sg=$(aws ec2 create-security-group \
  --group-name db-sg \
  --description "Database security group" \
  --vpc-id $vpc_id \
  --query 'GroupId' \
  --output text)

# Allow MySQL from web tier
aws ec2 authorize-security-group-ingress \
  --group-id $db_sg \
  --protocol tcp \
  --port 3306 \
  --source-group $sg  # Allow from web-sg

# ALB security group
alb_sg=$(aws ec2 create-security-group \
  --group-name alb-sg \
  --description "ALB security group" \
  --vpc-id $vpc_id \
  --query 'GroupId' \
  --output text)

# Allow HTTP/HTTPS to ALB
aws ec2 authorize-security-group-ingress \
  --group-id $alb_sg \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0

# Allow from ALB to web servers
aws ec2 authorize-security-group-ingress \
  --group-id $sg \
  --protocol tcp \
  --port 8080 \
  --source-group $alb_sg
```

## NACLs (Network Access Control Lists)

Stateless firewall at subnet level (rarely needed — security groups usually sufficient).

### Create NACL
```bash
nacl=$(aws ec2 create-network-acl \
  --vpc-id $vpc_id \
  --tag-specifications 'ResourceType=network-acl,Tags=[{Key=Name,Value=app-nacl}]' \
  --query 'NetworkAcl.NetworkAclId' \
  --output text)

# Allow inbound HTTP from 10.0.0.0/16
aws ec2 create-network-acl-entry \
  --network-acl-id $nacl \
  --rule-number 100 \
  --protocol tcp \
  --port-range From=80,To=80 \
  --cidr-block 10.0.0.0/16 \
  --ingress

# Allow ephemeral ports (1024-65535) for responses
aws ec2 create-network-acl-entry \
  --network-acl-id $nacl \
  --rule-number 110 \
  --protocol tcp \
  --port-range From=1024,To=65535 \
  --cidr-block 0.0.0.0/0 \
  --ingress

# Deny everything else (implicit)
```

## VPC Peering

Connect two VPCs privately.

```bash
# Create peering connection (accepter account accepts in parallel)
pcx=$(aws ec2 create-vpc-peering-connection \
  --vpc-id $vpc_id \
  --peer-vpc-id vpc-87654321 \
  --peer-owner-id 123456789012 \
  --query 'VpcPeeringConnection.VpcPeeringConnectionId' \
  --output text)

# Accept peering (in peer account)
aws ec2 accept-vpc-peering-connection --vpc-peering-connection-id $pcx

# Add routes in both VPCs
aws ec2 create-route \
  --route-table-id $pub_rt \
  --destination-cidr-block 10.1.0.0/16 \
  --vpc-peering-connection-id $pcx
```

## Transit Gateway

Connect multiple VPCs and on-premises networks.

```bash
# Create transit gateway
tgw=$(aws ec2 create-transit-gateway \
  --description "Production TGW" \
  --options AmazonSideAsn=64512 \
  --tag-specifications 'ResourceType=transit-gateway,Tags=[{Key=Name,Value=prod-tgw}]' \
  --query 'TransitGateway.TransitGatewayId' \
  --output text)

# Create TGW attachment (VPC)
tgw_attach=$(aws ec2 create-transit-gateway-vpc-attachment \
  --transit-gateway-id $tgw \
  --vpc-id $vpc_id \
  --subnet-ids $priv_subnet \
  --tag-specifications 'ResourceType=transit-gateway-attachment,Tags=[{Key=Name,Value=prod-attach}]' \
  --query 'TransitGatewayVpcAttachment.TransitGatewayAttachmentId' \
  --output text)

# Add route to TGW
aws ec2 create-route \
  --route-table-id $priv_rt \
  --destination-cidr-block 10.1.0.0/16 \
  --transit-gateway-id $tgw
```

## VPC Endpoints

Access AWS services privately without NAT.

### S3 Gateway Endpoint
```bash
s3_endpoint=$(aws ec2 create-vpc-endpoint \
  --vpc-id $vpc_id \
  --service-name com.amazonaws.us-east-1.s3 \
  --route-table-ids $priv_rt \
  --policy-text file://s3-endpoint-policy.json \
  --query 'VpcEndpoint.VpcEndpointId' \
  --output text)

# Endpoint policy (allow all S3)
cat > s3-endpoint-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:*",
      "Resource": "*"
    }
  ]
}
EOF
```

### Interface Endpoint (EC2, RDS, etc.)
```bash
# Create interface endpoint for RDS
rds_endpoint=$(aws ec2 create-vpc-endpoint \
  --vpc-id $vpc_id \
  --service-name com.amazonaws.us-east-1.rds \
  --vpc-endpoint-type Interface \
  --subnet-ids $priv_subnet \
  --security-group-ids $sg \
  --query 'VpcEndpoint.VpcEndpointId' \
  --output text)

# Connect to RDS via endpoint (private DNS)
# mysql -h rds.us-east-1.vpce.amazonaws.com
```

## PrivateLink

Expose services securely to other VPCs.

```bash
# Create network load balancer
nlb=$(aws elbv2 create-load-balancer \
  --name my-service-nlb \
  --subnets $priv_subnet \
  --type network \
  --scheme internal \
  --query 'LoadBalancers[0].LoadBalancerArn' \
  --output text)

# Create endpoint service
svc=$(aws ec2 create-vpc-endpoint-service-configuration \
  --network-load-balancer-arns $nlb \
  --acceptance-required \
  --query 'ServiceConfiguration.ServiceName' \
  --output text)

echo "Share this service name: $svc"
```

## Best Practices

1. **Separate public/private subnets**: Public for ALB, private for compute
2. **Multiple AZs**: Deploy across at least 2 AZs for HA
3. **Use NAT Gateway**: Prefer NAT Gateway over NAT Instance
4. **Security groups by tier**: Web tier, app tier, database tier
5. **VPC Flow Logs**: Monitor traffic for troubleshooting
6. **Use private subnets**: Keep databases/servers private when possible
7. **Transit Gateway**: Simplify multi-VPC connectivity
8. **VPC Endpoints**: Reduce NAT costs for AWS service access
