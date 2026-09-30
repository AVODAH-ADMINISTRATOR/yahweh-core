# Role-Based Access Control (RBAC) Policy

## 1. Overview
Security is a foundational pillar of the Biblical Language Translation Engine. This document outlines the RBAC matrices for the development repository, staging environments, and production.

## 2. Roles & Permissions

### 2.1. Developer
- **Access:** Read/Write access to non-production source code branches.
- **Capabilities:** Can create PRs, run local Docker environments, and trigger CI pipelines on feature branches.
- **Restrictions:** Cannot push directly to `main`. Cannot access production databases or staging secrets.

### 2.2. Reviewer / Theologian
- **Access:** Read access to source code. Write access to translation corpora and theological guardrail configurations.
- **Capabilities:** Approve PRs related to NLP model weights, translation dictionaries, and textual variant matrices.
- **Restrictions:** Cannot modify core infrastructure or deployment pipelines.

### 2.3. DevOps Engineer
- **Access:** Full access to infrastructure repositories, CI/CD configurations, and staging/production clusters.
- **Capabilities:** Deploy updates, manage Kubernetes manifests, manage secrets, and configure database access.
- **Restrictions:** Cannot unilaterally approve theological or linguistic changes.

### 2.4. Administrator (Advisory Board)
- **Access:** Global Read access. Final approval authority on `main` branch merges.
- **Capabilities:** Emergency break-glass access to all environments. Oversees immutable auditing logs.

## 3. Implementation
- **GitHub:** Branch protection rules require at least 2 reviews (including one Theologian for linguistic changes).
- **Kubernetes:** RBAC is enforced via ServiceAccounts, Roles, and RoleBindings in the `staging` and `production` namespaces.
