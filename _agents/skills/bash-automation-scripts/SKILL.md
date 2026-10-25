---
skill_name: bash-automation-scripts
description: Bash scripting patterns for error handling, argument parsing, logging, and parallel execution
category: Cloud & DevOps
version: 1.0.0
---

# Bash Automation Scripts

## Error Handling

```bash
#!/bin/bash
set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Custom error handler
trap 'echo "Error on line $LINENO"' ERR

# Function with error checking
deploy_app() {
    local env=$1

    if [[ -z "$env" ]]; then
        echo "Error: environment required" >&2
        return 1
    fi

    # Command with fallback
    local version=$(git describe --tags 2>/dev/null || echo "unknown")

    docker build -t myapp:$version .
    if [[ $? -ne 0 ]]; then
        echo "Build failed" >&2
        exit 1
    fi

    docker push myapp:$version
}

# Call with error handling
if ! deploy_app "$@"; then
    exit 1
fi
```

## Argument Parsing

```bash
#!/bin/bash

while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -v|--version)
            VERSION="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 -e ENV -v VERSION"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Validate required arguments
: ${ENVIRONMENT:?}
: ${VERSION:?}

echo "Deploying $VERSION to $ENVIRONMENT"
```

## Logging

```bash
#!/bin/bash

LOG_FILE="/var/log/deploy.log"
LOG_LEVEL=${LOG_LEVEL:-INFO}

log() {
    local level=$1
    shift
    local message="$@"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$level] $message" | tee -a "$LOG_FILE"
}

log_info() { log "INFO" "$@"; }
log_warn() { log "WARN" "$@"; }
log_error() { log "ERROR" "$@"; }

log_info "Starting deployment"
log_warn "This might take a while"
log_error "Something went wrong"
```

## Parallel Execution

```bash
#!/bin/bash

# Run jobs in parallel with GNU Parallel
export -f deploy_app

environments=(dev staging prod)

# Method 1: GNU Parallel
parallel deploy_app {} ::: "${environments[@]}"

# Method 2: Background jobs
for env in "${environments[@]}"; do
    deploy_app "$env" &
done
wait  # Wait for all background jobs

# Method 3: xargs for parallelization
echo "${environments[@]}" | xargs -P 3 -I {} bash -c 'deploy_app "$@"' _ {}

# Control parallelism
max_jobs=5
active=0
for env in "${environments[@]}"; do
    while [[ $active -ge $max_jobs ]]; do
        wait -n
        ((active--))
    done
    deploy_app "$env" &
    ((active++))
done
wait
```

## File Operations

```bash
#!/bin/bash

# Safe file operations
create_if_not_exists() {
    local file=$1
    if [[ ! -f "$file" ]]; then
        mkdir -p "$(dirname "$file")"
        touch "$file"
        log_info "Created $file"
    fi
}

# Recursive file processing
process_files() {
    local dir=$1
    local pattern=$2

    find "$dir" -type f -name "$pattern" -print0 | while IFS= read -r -d '' file; do
        # Process each file
        log_info "Processing $file"
        # operations...
    done
}

# Safe move/backup
backup_file() {
    local file=$1
    if [[ -f "$file" ]]; then
        mv "$file" "${file}.bak.$(date +%s)"
        log_info "Backed up $file"
    fi
}
```

## String Operations

```bash
#!/bin/bash

# String manipulation
str="hello-world-test"

# Length
echo ${#str}  # 15

# Substring
echo ${str:0:5}  # hello
echo ${str: -4}  # test

# Replace
echo ${str/world/universe}  # hello-universe-test
echo ${str//-/_}  # hello_world_test

# Remove prefix/suffix
echo ${str#hello-}  # world-test
echo ${str%-test}  # hello-world

# Convert case
echo ${str^^}  # HELLO-WORLD-TEST
echo ${str,,}  # hello-world-test

# Check containment
if [[ "$str" == *"world"* ]]; then
    echo "Contains world"
fi
```

## Network Operations

```bash
#!/bin/bash

# Check connectivity
check_service() {
    local host=$1
    local port=$2

    if nc -z "$host" "$port" 2>/dev/null; then
        log_info "$host:$port is reachable"
        return 0
    else
        log_error "$host:$port is not reachable"
        return 1
    fi
}

# Retry with backoff
retry_with_backoff() {
    local max_attempts=5
    local delay=1
    local attempt=1

    while [[ $attempt -le $max_attempts ]]; do
        if "$@"; then
            return 0
        fi

        log_warn "Attempt $attempt failed, retrying in ${delay}s..."
        sleep "$delay"
        delay=$((delay * 2))
        ((attempt++))
    done

    log_error "All $max_attempts attempts failed"
    return 1
}

# Usage
retry_with_backoff curl -f https://api.example.com/health
```

## Advanced Patterns

```bash
#!/bin/bash

# Process substitution
diff <(aws ec2 describe-instances --region us-east-1) \
     <(aws ec2 describe-instances --region us-west-2)

# Temporary files
tmpdir=$(mktemp -d)
trap "rm -rf $tmpdir" EXIT

# Here documents
cat > "$tmpdir/config.json" << 'EOF'
{
  "environment": "prod",
  "replicas": 3
}
EOF

# Array operations
declare -a servers=("web-1" "web-2" "web-3")
for server in "${servers[@]}"; do
    ssh "$server" "systemctl restart app"
done

# Associative arrays
declare -A config
config[db_host]="localhost"
config[db_port]="5432"
echo "Connecting to ${config[db_host]}:${config[db_port]}"

# Check command existence
if command -v docker &> /dev/null; then
    log_info "Docker is installed"
fi
```

## Testing Bash Scripts

```bash
# Using BATS (Bash Automated Testing System)
@test "deploy_app handles invalid env" {
    run deploy_app ""
    [[ $status -eq 1 ]]
}

@test "deploy_app creates docker image" {
    run deploy_app "dev"
    [[ $status -eq 0 ]]
    [[ $output == *"Successfully built"* ]]
}
```

## Best Practices

1. **Always use set -euo pipefail**: Fail on errors
2. **Quote variables**: Prevent word splitting
3. **Error handling**: Trap and log errors
4. **Validation**: Check arguments early
5. **Logging**: Structured logging with levels
6. **Parallel execution**: Control concurrency
7. **Cleanup**: Use trap for cleanup
8. **Testing**: Test scripts with BATS
9. **Documentation**: Comments for complex logic
10. **Reusability**: Functions for common operations
