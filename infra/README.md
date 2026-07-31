# Infrastructure

Terraform for GCP resources — projects, Cloud Run services, Cloud Run
Jobs, Cloud SQL, Pub/Sub topics/subscriptions, GCS buckets, IAM,
Artifact Registry, secrets. See
[`docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md) §10.

Environments: `dev`, `staging`, `prod` as separate GCP projects, one
Terraform workspace each.

Nothing is scaffolded yet — this PR only defines the layout. First
Terraform will land alongside Phase A in
[`docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md) §15.
