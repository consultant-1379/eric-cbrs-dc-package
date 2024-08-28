{{/*
Expand the name of the chart.
*/}}
{{- define "eric-cbrs-dc-package.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "eric-cbrs-dc-package.version" -}}
{{- printf "%s" .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}


{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "eric-cbrs-dc-package.fullname" -}}
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
{{- define "eric-cbrs-dc-package.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
*/}}
{{- define "eric-cbrs-dc-package.hook.image" -}}
    {{- $registryUrl := (index .Values "uninstall" "image" "registry") }}
    {{- if .Values.global -}}
        {{- if .Values.global.registry -}}
            {{- if .Values.global.registry.url -}}
                {{- $registryUrl = .Values.global.registry.url -}}
            {{- end -}}
        {{- end -}}
    {{- end -}}
    {{- printf "%s/%s/%s:%s" $registryUrl (index .Values "uninstall" "image" "repoPath") (index .Values "uninstall" "image" "name") (index .Values "uninstall" "image" "version") }}
{{- end }}

{{/*
*/}}
{{- define "eric-cbrs-dc-package.hook.imagePullPolicy" -}}
{{- (index .Values "uninstall" "image" "imagePullPolicy") }}
{{- end }}

{{/*
*/}}
{{- define "eric-cbrs-dc-package.cmyp-brm-user" -}}
{{- (index .Values "cmyp-brm" "user") }}
{{- end }}

{{/*
*/}}
{{- define "eric-cbrs-dc-package.cmyp-brm-encryptedPass" -}}
{{- (index .Values "cmyp-brm" "encryptedPass") }}
{{- end }}

{{/*
Create annotation for the product information (DR-D1121-064, DR-D1121-067)
*/}}
{{- define "eric-cbrs-dc-package.product-info" -}}
ericsson.com/product-name: {{ (fromYaml (.Files.Get "eric-product-info.yaml")).productName | quote }}
ericsson.com/product-number: {{ (fromYaml (.Files.Get "eric-product-info.yaml")).productNumber | quote }}
ericsson.com/product-type: {{ (fromYaml (.Files.Get "eric-product-info.yaml")).productType | quote }}
ericsson.com/product-description: {{ (fromYaml (.Files.Get "eric-product-info.yaml")).description | quote }}
ericsson.com/production-date: {{ .Values.productInfo.date | quote }}
ericsson.com/product-revision: {{ .Values.productInfo.productSet | quote }}
meta.helm.sh/release-namespace: {{ .Release.Namespace }}
meta.helm.sh/release-name: {{ .Release.Name }}
{{- end}}

{/*
Create a user defined annotation (DR-D1121-065, DR-D1121-060)
*/}}
{{ define "eric-cbrs-dc-package.config-annotations" }}
  {{- $global := (.Values.global).annotations -}}
  {{- $service := .Values.annotations -}}
  {{- include "eric-cbrs-dc-package.mergeAnnotations" (dict "location" .Template.Name "sources" (list $global $service)) | trim }}
{{- end }}

{{/*
Merged annotations for Default, which includes productInfo and config
*/}}
{{- define "eric-cbrs-dc-package.annotations" -}}
  {{- $productInfo := include "eric-cbrs-dc-package.product-info" . | fromYaml -}}
  {{- $config := include "eric-cbrs-dc-package.config-annotations" . | fromYaml -}}
  {{- include "eric-cbrs-dc-package.mergeAnnotations" (dict "location" .Template.Name "sources" (list $productInfo $config)) | trim }}
{{- end -}}

{{- define "eric-cbrs-dc-package.helm-annotations" -}}
{{- $helmHooks := dict -}}
{{- $_ := set $helmHooks "helm.sh/hook" "post-delete" -}}
{{- $_ := set $helmHooks "helm.sh/hook-delete-policy" "before-hook-creation,hook-succeeded,hook-failed" -}}
{{- $_ := set $helmHooks "helm.sh/hook-weight" "98" -}}
{{- $commonAnn := fromYaml (include "eric-cbrs-dc-package.annotations" .) -}}
{{- include "eric-cbrs-dc-package.mergeAnnotations" (dict "location" .Template.Name "sources" (list $helmHooks $commonAnn)) | nindent 4 }}
{{- end -}}

{{- define "eric-cbrs-dc-package.hook-annotations" -}}
  {{- $helmHooks := include "eric-cbrs-dc-package.helm-annotations" . | fromYaml -}}
  {{- $config := include "eric-cbrs-dc-package.annotations" . | fromYaml -}}
  {{- include "eric-cbrs-dc-package.mergeAnnotations" (dict "location" .Template.Name "sources" (list $helmHooks $config)) | trim -}}
{{- end -}}

{{/*
*/}}
{{- define "eric-cbrs-dc-package.search-engine-template-job.image" -}}
    {{- $registryUrl := (index .Values "eric-cbrs-search-engine-template-job" "image" "registry") }}
    {{- if .Values.global -}}
        {{- if .Values.global.registry -}}
            {{- if .Values.global.registry.url -}}
                {{- $registryUrl = .Values.global.registry.url -}}
            {{- end -}}
        {{- end -}}
    {{- end -}}
    {{- printf "%s/%s/%s:%s" $registryUrl (index .Values "eric-cbrs-search-engine-template-job" "image" "repoPath") (index .Values "eric-cbrs-search-engine-template-job" "image" "name") (index .Values "eric-cbrs-search-engine-template-job" "image" "tag") }}
{{- end }}

{{/*
*/}}
{{- define "eric-cbrs-dc-package.search-engine-template-job.imagePullPolicy" -}}
{{- (index .Values "eric-cbrs-search-engine-template-job" "image" "imagePullPolicy") }}
{{- end }}

{{/*
Create the security policy rolebinding name according to DR-D1123-134.
*/}}
{{- define "eric-cbrs-dc-package.security-policy-rolebinding.name" -}}
{{- if .Values.global -}}
{{- if .Values.global.securityPolicy -}}
{{ if eq .Values.global.securityPolicy.rolekind "" }}
    {{- printf "%s-%s-sp" (include "eric-cbrs-dc-package.service-account.name" .) ( .Values.securityPolicy.rolename ) | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{ if ne .Values.global.securityPolicy.rolekind "" }}
    {{- printf "%s-%s-%s-sp" (include "eric-cbrs-dc-package.service-account.name" .) (include "eric-cbrs-dc-package.rolekind" . ) ( .Values.securityPolicy.rolename )  | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- end -}}
{{- end -}}

{{- define "eric-cbrs-dc-package.service-account.name" -}}
    {{- printf "%s-service-account" (include "eric-cbrs-dc-package.name" .) | trimSuffix "-" -}}
{{- end -}}

{{/*
Create the security policy rolekind.
*/}}
{{- define "eric-cbrs-dc-package.rolekind" -}}
{{- if .Values.global -}}
{{- if .Values.global.securityPolicy -}}
{{ if eq .Values.global.securityPolicy.rolekind "ClusterRole" }}
    {{- printf  "c" -}}
{{- end -}}
{{ if eq .Values.global.securityPolicy.rolekind "Role" }}
    {{- printf  "r" -}}
{{- end -}}
{{- end -}}
{{- end -}}
{{- end -}}