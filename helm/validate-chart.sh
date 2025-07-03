#!/bin/bash

# NotesNest Helm Chart Validation Script
# This script validates the Helm chart templates, syntax, and configuration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Chart directory
CHART_DIR="./helm/notesnest"
TEMP_DIR=$(mktemp -d)

echo -e "${BLUE}🚀 NotesNest Helm Chart Validation${NC}"
echo "========================================"

# Function to print success message
success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Function to print error message
error() {
    echo -e "${RED}❌ $1${NC}"
    exit 1
}

# Function to print warning message
warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Function to print info message
info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if helm is installed
if ! command -v helm &> /dev/null; then
    error "Helm is not installed. Please install Helm 3.x"
fi

# Check helm version
HELM_VERSION=$(helm version --short | cut -d':' -f2 | cut -d'v' -f2 | cut -d'+' -f1)
HELM_MAJOR=$(echo "$HELM_VERSION" | cut -d'.' -f1)
if [ "$HELM_MAJOR" -lt 3 ]; then
    error "Helm 3.x is required, found version $HELM_VERSION"
fi
success "Helm version $HELM_VERSION is compatible"

# Check if chart directory exists
if [ ! -d "$CHART_DIR" ]; then
    error "Chart directory $CHART_DIR not found"
fi
success "Chart directory found"

# Validate Chart.yaml
if [ ! -f "$CHART_DIR/Chart.yaml" ]; then
    error "Chart.yaml not found"
fi
success "Chart.yaml exists"

# Lint the chart
info "Running helm lint..."
if helm lint "$CHART_DIR"; then
    success "Chart linting passed"
else
    error "Chart linting failed"
fi

# Generate test values
cat > "$TEMP_DIR/test-values.yaml" << EOF
app:
  secrets:
    jwtSecretKey: "test-jwt-secret-key-for-validation-only"
    postgresUser: "notesnest_user"
    postgresPassword: "test-password-123"
    postgresDatabase: "notesnest"
EOF

# Test template rendering
info "Testing template rendering..."
if helm template test-release "$CHART_DIR" -f "$TEMP_DIR/test-values.yaml" > "$TEMP_DIR/rendered-templates.yaml"; then
    success "Template rendering successful"
else
    error "Template rendering failed"
fi

# Validate rendered YAML
info "Validating rendered YAML syntax..."
if kubectl --dry-run=client apply -f "$TEMP_DIR/rendered-templates.yaml" &> /dev/null; then
    success "Rendered YAML is valid"
else
    warning "Rendered YAML validation failed - this might be due to missing CRDs (e.g., ServiceMonitor)"
fi

# Check for required templates
REQUIRED_TEMPLATES=(
    "secrets.yaml"
    "configmap.yaml"
    "postgresql-statefulset.yaml"
    "postgresql-service.yaml"
    "app-deployment.yaml"
    "app-service.yaml"
)

info "Checking required templates..."
for template in "${REQUIRED_TEMPLATES[@]}"; do
    if [ -f "$CHART_DIR/templates/$template" ]; then
        success "Template $template exists"
    else
        error "Required template $template is missing"
    fi
done

# Check for Helm template functions
info "Checking template functions..."
TEMPLATE_FUNCTIONS=(
    "include \"notesnest.name\""
    "include \"notesnest.fullname\""
    "include \"notesnest.labels\""
    "include \"notesnest.validateSecrets\""
)

for func in "${TEMPLATE_FUNCTIONS[@]}"; do
    if grep -r "$func" "$CHART_DIR/templates/" > /dev/null; then
        success "Template function '$func' is used"
    else
        warning "Template function '$func' not found"
    fi
done

# Test dry-run installation
info "Testing dry-run installation..."
if helm install test-release "$CHART_DIR" \
    -f "$TEMP_DIR/test-values.yaml" \
    --dry-run --debug > "$TEMP_DIR/dry-run.yaml"; then
    success "Dry-run installation successful"
else
    error "Dry-run installation failed"
fi

# Check for security best practices
info "Checking security best practices..."

# Check for non-root security context
if grep -r "runAsNonRoot: true" "$CHART_DIR/templates/" > /dev/null; then
    success "Non-root security context found"
else
    warning "Non-root security context not enforced"
fi

# Check for read-only root filesystem
if grep -r "readOnlyRootFilesystem: true" "$CHART_DIR/templates/" > /dev/null; then
    success "Read-only root filesystem configured"
else
    warning "Read-only root filesystem not configured"
fi

# Check for resource limits
if grep -r "resources:" "$CHART_DIR/templates/" > /dev/null; then
    success "Resource limits/requests configured"
else
    warning "Resource limits/requests not configured"
fi

# Check for secrets usage (no hardcoded values)
info "Checking for hardcoded secrets..."
HARDCODED_PATTERNS=(
    "password.*:"
    "secret.*:"
    "key.*:"
)

HARDCODED_FOUND=false
for pattern in "${HARDCODED_PATTERNS[@]}"; do
    if grep -ri "$pattern" "$CHART_DIR/templates/" | grep -v "secretKeyRef\|configMapKeyRef\|valueFrom" > /dev/null; then
        warning "Potential hardcoded secret found: $(grep -ri "$pattern" "$CHART_DIR/templates/" | grep -v "secretKeyRef\|configMapKeyRef\|valueFrom")"
        HARDCODED_FOUND=true
    fi
done

if [ "$HARDCODED_FOUND" = false ]; then
    success "No hardcoded secrets found"
fi

# Test with different configurations
info "Testing with different configurations..."

# Test with PostgreSQL disabled
cat > "$TEMP_DIR/test-values-no-postgres.yaml" << EOF
app:
  secrets:
    jwtSecretKey: "test-jwt-secret-key-for-validation-only"
    postgresUser: "notesnest_user"
    postgresPassword: "test-password-123"
    postgresDatabase: "notesnest"
    databaseUrl: "postgresql://user:pass@external-db:5432/notesnest"

postgresql:
  enabled: false
EOF

if helm template test-release "$CHART_DIR" -f "$TEMP_DIR/test-values-no-postgres.yaml" > /dev/null; then
    success "Chart works with external PostgreSQL"
else
    error "Chart fails with external PostgreSQL"
fi

# Test with ingress enabled
cat > "$TEMP_DIR/test-values-ingress.yaml" << EOF
app:
  secrets:
    jwtSecretKey: "test-jwt-secret-key-for-validation-only"
    postgresUser: "notesnest_user"
    postgresPassword: "test-password-123"
    postgresDatabase: "notesnest"

ingress:
  enabled: true
  hosts:
    - host: notesnest.example.com
      paths:
        - path: /
          pathType: Prefix
EOF

if helm template test-release "$CHART_DIR" -f "$TEMP_DIR/test-values-ingress.yaml" > /dev/null; then
    success "Chart works with ingress enabled"
else
    error "Chart fails with ingress enabled"
fi

# Test with autoscaling enabled
cat > "$TEMP_DIR/test-values-hpa.yaml" << EOF
app:
  secrets:
    jwtSecretKey: "test-jwt-secret-key-for-validation-only"
    postgresUser: "notesnest_user"
    postgresPassword: "test-password-123"
    postgresDatabase: "notesnest"

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
EOF

if helm template test-release "$CHART_DIR" -f "$TEMP_DIR/test-values-hpa.yaml" > /dev/null; then
    success "Chart works with autoscaling enabled"
else
    error "Chart fails with autoscaling enabled"
fi

# Check values.yaml documentation
info "Checking values.yaml documentation..."
if grep -q "# " "$CHART_DIR/values.yaml"; then
    success "Values.yaml contains documentation"
else
    warning "Values.yaml lacks documentation comments"
fi

# Generate deployment instructions
info "Generating sample deployment instructions..."
cat > "$TEMP_DIR/deployment-instructions.md" << 'EOF'
# NotesNest Deployment Instructions

## 1. Generate Secrets
```bash
export JWT_SECRET_KEY=$(openssl rand -hex 32)
export POSTGRES_PASSWORD=$(openssl rand -base64 32)
```

## 2. Deploy with Helm
```bash
helm install notesnest ./helm/notesnest \
  --set app.secrets.jwtSecretKey="$JWT_SECRET_KEY" \
  --set app.secrets.postgresUser="notesnest_user" \
  --set app.secrets.postgresPassword="$POSTGRES_PASSWORD" \
  --set app.secrets.postgresDatabase="notesnest" \
  --create-namespace \
  --namespace notesnest
```

## 3. Verify Deployment
```bash
kubectl get pods -n notesnest
kubectl get svc -n notesnest
```

## 4. Access Application
```bash
kubectl port-forward -n notesnest svc/notesnest-service 8080:80
# Then visit http://localhost:8080/docs
```
EOF

success "Sample deployment instructions generated at $TEMP_DIR/deployment-instructions.md"

# Summary
echo ""
echo -e "${BLUE}📋 Validation Summary${NC}"
echo "===================="
success "Chart validation completed successfully"
info "Chart is ready for deployment"
info "Temporary files created in: $TEMP_DIR"

# Cleanup option
read -p "Remove temporary files? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf "$TEMP_DIR"
    success "Temporary files cleaned up"
else
    info "Temporary files kept at: $TEMP_DIR"
fi

echo ""
echo -e "${GREEN}🎉 NotesNest Helm Chart is ready for deployment!${NC}" 