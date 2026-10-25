---
skill_name: AWS ECS Fargate Guide
description: Deploy containerized applications with task definitions, services, load balancing, and auto-scaling
category: DevOps
version: 1.0.0
---

# AWS ECS Fargate Guide

## Overview
ECS Fargate provides serverless container orchestration without managing EC2 instances. Deploy and scale containerized applications with built-in integration to load balancers and auto-scaling.

## Cluster Setup

### Create Fargate Cluster

```hcl
resource "aws_ecs_cluster" "main" {
  name = "production-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

resource "aws_ecs_cluster_capacity_providers" "main" {
  cluster_name = aws_ecs_cluster.main.name

  capacity_providers = ["FARGATE", "FARGATE_SPOT"]

  default_capacity_provider_strategy {
    base              = 1
    weight            = 100
    capacity_provider = "FARGATE"
  }
}
```

## Task Definition

### Create Task Definition

```hcl
resource "aws_ecs_task_definition" "app" {
  family                   = "my-app"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.ecs_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name      = "my-app"
      image     = "123456789012.dkr.ecr.us-east-1.amazonaws.com/my-app:latest"
      cpu       = 256
      memory    = 512
      essential = true

      portMappings = [
        {
          containerPort = 8080
          hostPort      = 8080
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "ENVIRONMENT"
          value = "production"
        },
        {
          name  = "LOG_LEVEL"
          value = "info"
        }
      ]

      secrets = [
        {
          name      = "DATABASE_URL"
          valueFrom = "arn:aws:secretsmanager:region:account:secret:db-url"
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/my-app"
          "awslogs-region"        = "us-east-1"
          "awslogs-stream-prefix" = "ecs"
        }
      }

      dependsOn = [
        {
          containerName = "dependency"
          condition     = "START"
        }
      ]
    }
  ])
}
```

## ECS Service

### Create Service with Load Balancer

```hcl
resource "aws_ecs_service" "app" {
  name            = "my-app-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.app.arn
  desired_count   = 2
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnets
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.app.arn
    container_name   = "my-app"
    container_port   = 8080
  }

  depends_on = [
    aws_lb_listener.app,
    aws_iam_role_policy.ecs_task_execution_role_policy
  ]

  deployment_configuration {
    maximum_percent         = 200
    minimum_healthy_percent = 100
  }
}
```

## Load Balancing

### Create Application Load Balancer

```hcl
resource "aws_lb" "main" {
  name               = "my-app-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = var.public_subnets
}

resource "aws_lb_target_group" "app" {
  name        = "my-app-tg"
  port        = 8080
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 3
    interval            = 30
    path                = "/health"
    matcher             = "200"
  }
}

resource "aws_lb_listener" "app" {
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }
}

resource "aws_lb_listener_rule" "https" {
  listener_arn = aws_lb_listener.app.arn
  priority     = 1

  action {
    type = "redirect"

    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }

  condition {
    path_pattern {
      values = ["*"]
    }
  }
}
```

## Auto-Scaling

### Service Auto-Scaling

```hcl
resource "aws_appautoscaling_target" "ecs_target" {
  max_capacity       = 10
  min_capacity       = 2
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.app.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "cpu_scaling" {
  policy_name               = "cpu-autoscaling"
  policy_type               = "TargetTrackingScaling"
  resource_id               = aws_appautoscaling_target.ecs_target.resource_id
  scalable_dimension        = aws_appautoscaling_target.ecs_target.scalable_dimension
  service_namespace         = aws_appautoscaling_target.ecs_target.service_namespace
  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value = 70.0
  }
}

resource "aws_appautoscaling_policy" "memory_scaling" {
  policy_name               = "memory-autoscaling"
  policy_type               = "TargetTrackingScaling"
  resource_id               = aws_appautoscaling_target.ecs_target.resource_id
  scalable_dimension        = aws_appautoscaling_target.ecs_target.scalable_dimension
  service_namespace         = aws_appautoscaling_target.ecs_target.service_namespace
  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageMemoryUtilization"
    }
    target_value = 80.0
  }
}
```

## Deployment Strategy

### Blue/Green Deployment

```python
import boto3

ecs = boto3.client('ecs')

def deploy_new_version(cluster, service, new_image):
    """Perform blue/green deployment"""
    # Get current task definition
    response = ecs.describe_services(
        cluster=cluster,
        services=[service]
    )
    current_td_arn = response['services'][0]['taskDefinition']

    # Register new task definition
    new_td = ecs.register_task_definition(
        family='my-app',
        # ... other params with new_image
    )

    # Update service
    ecs.update_service(
        cluster=cluster,
        service=service,
        taskDefinition=new_td['taskDefinition']['taskDefinitionArn'],
        deploymentConfiguration={
            'maximumPercent': 200,
            'minimumHealthyPercent': 100,
            'deploymentCircuitBreaker': {
                'enable': True,
                'rollback': True
            }
        }
    )

    return new_td['taskDefinition']['taskDefinitionArn']
```

## Logging and Monitoring

### CloudWatch Logs

```hcl
resource "aws_cloudwatch_log_group" "ecs" {
  name              = "/ecs/my-app"
  retention_in_days = 30
}

resource "aws_cloudwatch_log_stream" "ecs" {
  name           = "ecs-stream"
  log_group_name = aws_cloudwatch_log_group.ecs.name
}
```

### Container Insights

```python
import boto3

cloudwatch = boto3.client('cloudwatch')

def get_container_metrics(cluster, service):
    """Get Container Insights metrics"""
    response = cloudwatch.get_metric_statistics(
        Namespace='ECS/ContainerInsights',
        MetricName='TaskCount',
        Dimensions=[
            {'Name': 'ClusterName', 'Value': cluster},
            {'Name': 'ServiceName', 'Value': service}
        ],
        StartTime=datetime.utcnow() - timedelta(hours=1),
        EndTime=datetime.utcnow(),
        Period=300,
        Statistics=['Average', 'Maximum']
    )
    return response['Datapoints']
```

## Task Execution

### Run Task

```python
import boto3

ecs = boto3.client('ecs')

def run_one_off_task(cluster, task_definition, command):
    """Run one-time task"""
    response = ecs.run_task(
        cluster=cluster,
        taskDefinition=task_definition,
        launchType='FARGATE',
        networkConfiguration={
            'awsvpcConfiguration': {
                'subnets': ['subnet-xxx'],
                'securityGroups': ['sg-xxx'],
                'assignPublicIp': 'DISABLED'
            }
        },
        overrides={
            'containerOverrides': [
                {
                    'name': 'my-app',
                    'command': command
                }
            ]
        }
    )
    return response['tasks'][0]['taskArn']
```

## Production Checklist

- [ ] Use Fargate for serverless container management
- [ ] Configure health checks on target groups
- [ ] Enable Container Insights monitoring
- [ ] Use CloudWatch for logging
- [ ] Implement auto-scaling policies
- [ ] Use task role for application permissions
- [ ] Store secrets in Secrets Manager
- [ ] Enable deployment circuit breaker
- [ ] Configure appropriate CPU/memory limits
- [ ] Use private subnets for tasks
- [ ] Set up ALB security groups
- [ ] Monitor task startup time
- [ ] Document environment variables
- [ ] Test deployments in staging first
