---
skill_name: Azure DevOps Pipelines
description: Build CI/CD pipelines with YAML syntax, multi-stage deployments, environments, approvals, and agent pools
category: DevOps
version: 1.0.0
---

# Azure DevOps Pipelines

## Overview
Azure Pipelines automate build, test, and deployment workflows. Master YAML syntax, stages, and environments for reliable delivery.

## YAML Pipeline Structure

### Basic Pipeline

```yaml
trigger:
  - main
  - develop

pr:
  - main

pool:
  vmImage: 'ubuntu-latest'

variables:
  buildConfiguration: 'Release'
  dotnetVersion: '8.0.x'

stages:
- stage: Build
  displayName: Build Stage
  jobs:
  - job: BuildJob
    displayName: Build Application
    steps:
    - task: UseDotNet@2
      inputs:
        version: $(dotnetVersion)

    - task: DotNetCoreCLI@2
      displayName: Restore Dependencies
      inputs:
        command: 'restore'
        projects: '**/*.csproj'

    - task: DotNetCoreCLI@2
      displayName: Build
      inputs:
        command: 'build'
        arguments: '--configuration $(buildConfiguration)'

    - task: DotNetCoreCLI@2
      displayName: Run Tests
      inputs:
        command: 'test'
        arguments: '--configuration $(buildConfiguration) --no-build'

    - task: DotNetCoreCLI@2
      displayName: Publish
      inputs:
        command: 'publish'
        arguments: '--configuration $(buildConfiguration) --output $(Build.ArtifactStagingDirectory)'
        publishWebProjects: true

    - task: PublishBuildArtifacts@1
      displayName: Publish Artifacts
      inputs:
        PathtoPublish: $(Build.ArtifactStagingDirectory)
        ArtifactName: drop
```

## Multi-Stage Deployments

### Deployment Pipeline

```yaml
stages:
- stage: Build
  displayName: Build Application
  jobs:
  - job: Build
    steps:
    - checkout: self
    - task: DotNetCoreCLI@2
      inputs:
        command: 'build'
    - publish: $(Build.SourcesDirectory)
      artifact: buildOutput

- stage: DeployDev
  displayName: Deploy to Development
  dependsOn: Build
  condition: succeeded()
  jobs:
  - deployment: DeployToAzureAppService
    displayName: Deploy to Dev
    environment: 'Development'
    strategy:
      runOnce:
        deploy:
          steps:
          - download: current
            artifact: buildOutput
          - task: AzureWebApp@1
            displayName: Deploy to Azure App Service
            inputs:
              azureSubscription: 'Azure Subscription'
              appName: 'my-app-dev'
              package: '$(Pipeline.Workspace)/buildOutput'

- stage: ApprovalStage
  displayName: Approve Production Deployment
  dependsOn: DeployDev
  condition: succeeded()
  jobs:
  - job: WaitForValidation
    displayName: Wait for Manual Approval
    pool: server
    steps:
    - task: ManualValidation@0
      inputs:
        notifyUsers: 'devops-team@company.com'
        instructions: 'Review deployment and approve'
        onTimeout: 'reject'

- stage: DeployProd
  displayName: Deploy to Production
  dependsOn: ApprovalStage
  condition: succeeded()
  jobs:
  - deployment: DeployToProduction
    displayName: Deploy to Production
    environment: 'Production'
    strategy:
      runOnce:
        pre:
          steps:
          - checkout: self
          - script: echo Creating deployment snapshot
        deploy:
          steps:
          - download: current
            artifact: buildOutput
          - task: AzureWebApp@1
            inputs:
              azureSubscription: 'Azure Subscription'
              appName: 'my-app-prod'
              package: '$(Pipeline.Workspace)/buildOutput'
        postDeploy:
          steps:
          - task: RunPostDeploymentTests@0
            inputs:
              testScript: 'tests/smoke-tests.sh'
```

## Environment Configuration

### Manage Environments

```yaml
stages:
- stage: Deploy
  jobs:
  - deployment: Deploy
    displayName: Deploy to Multiple Environments
    environment:
      name: Production
      resourceType: VirtualMachine
      tags: web
    strategy:
      runOnce:
        deploy:
          steps:
          - script: echo Deploying to environment
          - task: Bash@3
            inputs:
              targetType: 'inline'
              script: 'echo Environment variables: $(ENVIRONMENT_VAR)'
            env:
              ENVIRONMENT_VAR: $(CUSTOM_VAR)
```

### Approval Gates

```yaml
stages:
- stage: Deploy
  jobs:
  - deployment: Deploy
    environment:
      name: Production
      resourceName: WebServer01
      resourceType: VirtualMachine
    strategy:
      runOnce:
        deploy:
          steps:
          - bash: echo Deployment succeeded

        # Pre-deployment approval
        preDeploy:
          steps:
          - task: ManualValidation@0
            inputs:
              notifyUsers: 'lead@company.com'
              instructions: 'Please review and approve'
              onTimeout: 'reject'

        # Post-deployment validation
        postDeploy:
          steps:
          - bash: |
              # Run health checks
              curl -f https://myapp.com/health
```

## Variables & Secrets

### Variable Management

```yaml
variables:
  buildConfiguration: Release
  environment: production

# Group variables
variables:
- group: Production-Secrets

stages:
- stage: Deploy
  displayName: Deploy
  variables:
    # Stage-level variables
    stageVar: value
  jobs:
  - job: Deploy
    variables:
      # Job-level variables override stage/global
      jobVar: value
    steps:
    - script: echo $(buildConfiguration)
    - script: echo $(connectionString)
      env:
        # Map secret variables
        ConnString: $(dbConnectionString)
```

### Secure Variable Injection

```yaml
steps:
- task: DownloadSecureFile@1
  displayName: Download Certificate
  inputs:
    secureFile: 'prod-cert.pfx'
    retryCount: '5'

- script: |
    # Use secure file
    openssl pkcs12 -in $(Agent.TempDirectory)/prod-cert.pfx -out cert.pem

- task: KeyVault@2
  displayName: Get Secrets from Key Vault
  inputs:
    azureSubscription: 'Azure Subscription'
    KeyVaultName: 'mykeyvault'
    SecretsFilter: 'api-key,db-password'
    RunAsPreJob: true
```

## Advanced Patterns

### Conditional Steps

```yaml
steps:
- task: PublishTestResults@2
  displayName: Publish Test Results
  condition: always()  # Run even if previous steps fail
  inputs:
    testResultsFormat: 'JUnit'
    testResultsFiles: '**/results.xml'

- script: echo Deployment succeeded
  condition: eq(variables['Build.SourceBranch'], 'refs/heads/main')

- task: SendEmail@1
  displayName: Notify on Failure
  condition: failed()
  inputs:
    to: 'alerts@company.com'
    subject: 'Pipeline Failed'
```

### Matrix Builds

```yaml
strategy:
  matrix:
    Python38:
      pythonVersion: '3.8'
    Python39:
      pythonVersion: '3.9'
    Python310:
      pythonVersion: '3.10'

steps:
- task: UsePythonVersion@0
  inputs:
    versionSpec: '$(pythonVersion)'

- script: python -m pytest tests/
```

## Custom Tasks & Templates

### Reusable Templates

```yaml
# templates/build-template.yml
parameters:
  configuration: 'Release'
  platform: 'x64'

jobs:
- job: Build
  displayName: Build ${{ parameters.configuration }}|${{ parameters.platform }}
  steps:
  - task: UseMSBuildTask@1
    inputs:
      version: '17.0'
  - task: MSBuild@1
    inputs:
      solution: '**/*.sln'
      configuration: ${{ parameters.configuration }}
      platform: ${{ parameters.platform }}

# azure-pipelines.yml
stages:
- stage: Build
  jobs:
  - template: templates/build-template.yml
    parameters:
      configuration: 'Debug'

  - template: templates/build-template.yml
    parameters:
      configuration: 'Release'
```

## Production Checklist

- [ ] Use YAML pipelines (not visual editor)
- [ ] Store secrets in Key Vault
- [ ] Implement multi-stage deployments
- [ ] Require manual approvals for production
- [ ] Use agent pools for security
- [ ] Version control all pipeline definitions
- [ ] Implement rollback procedures
- [ ] Monitor pipeline execution times
- [ ] Set up failure notifications
- [ ] Document custom tasks and templates
