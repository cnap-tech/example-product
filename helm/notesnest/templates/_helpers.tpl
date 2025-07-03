{{/*
Expand the name of the chart.
*/}}
{{- define "notesnest.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "notesnest.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "notesnest.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "notesnest.labels" -}}
helm.sh/chart: {{ include "notesnest.chart" . }}
{{ include "notesnest.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "notesnest.selectorLabels" -}}
app.kubernetes.io/name: {{ include "notesnest.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
App-specific labels
*/}}
{{- define "notesnest.app.labels" -}}
{{ include "notesnest.labels" . }}
app.kubernetes.io/component: application
{{- end }}

{{/*
App selector labels
*/}}
{{- define "notesnest.app.selectorLabels" -}}
{{ include "notesnest.selectorLabels" . }}
app.kubernetes.io/component: application
{{- end }}

{{/*
PostgreSQL labels
*/}}
{{- define "notesnest.postgresql.labels" -}}
{{ include "notesnest.labels" . }}
app.kubernetes.io/component: database
{{- end }}

{{/*
PostgreSQL selector labels
*/}}
{{- define "notesnest.postgresql.selectorLabels" -}}
{{ include "notesnest.selectorLabels" . }}
app.kubernetes.io/component: database
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "notesnest.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "notesnest.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
PostgreSQL service name
*/}}
{{- define "notesnest.postgresql.serviceName" -}}
{{- printf "%s-postgresql" (include "notesnest.fullname" .) }}
{{- end }}

{{/*
PostgreSQL StatefulSet name
*/}}
{{- define "notesnest.postgresql.fullname" -}}
{{- printf "%s-postgresql" (include "notesnest.fullname" .) }}
{{- end }}

{{/*
Database URL for the application
*/}}
{{- define "notesnest.databaseUrl" -}}
{{- if .Values.app.secrets.databaseUrl }}
{{- .Values.app.secrets.databaseUrl }}
{{- else }}
{{- printf "postgresql://%s:%s@%s:5432/%s" .Values.postgresql.database.user .Values.app.secrets.postgresPassword (include "notesnest.postgresql.serviceName" .) .Values.postgresql.database.name }}
{{- end }}
{{- end }}

{{/*
Validate required secrets
*/}}
{{- define "notesnest.validateSecrets" -}}
{{- if not .Values.app.secrets.jwtSecretKey }}
{{- fail "app.secrets.jwtSecretKey is required. Generate with: openssl rand -hex 32" }}
{{- end }}
{{- if not .Values.app.secrets.postgresPassword }}
{{- fail "app.secrets.postgresPassword is required" }}
{{- end }}
{{- if not .Values.app.secrets.postgresUser }}
{{- fail "app.secrets.postgresUser is required" }}
{{- end }}
{{- if not .Values.app.secrets.postgresDatabase }}
{{- fail "app.secrets.postgresDatabase is required" }}
{{- end }}
{{- end }}

{{/*
Security context for application pods
*/}}
{{- define "notesnest.app.securityContext" -}}
securityContext:
  runAsNonRoot: true
  runAsUser: {{ .Values.global.securityContext.runAsUser }}
  fsGroup: {{ .Values.global.securityContext.fsGroup }}
  capabilities:
    drop:
    - ALL
  readOnlyRootFilesystem: true
  allowPrivilegeEscalation: false
{{- end }}

{{/*
Security context for PostgreSQL pods
*/}}
{{- define "notesnest.postgresql.securityContext" -}}
securityContext:
  runAsUser: {{ .Values.postgresql.securityContext.runAsUser }}
  runAsGroup: {{ .Values.postgresql.securityContext.runAsGroup }}
  fsGroup: {{ .Values.postgresql.securityContext.fsGroup }}
  capabilities:
    drop:
    - ALL
  readOnlyRootFilesystem: false
  allowPrivilegeEscalation: false
{{- end }} 