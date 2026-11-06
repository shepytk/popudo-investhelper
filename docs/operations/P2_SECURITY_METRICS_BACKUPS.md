# P2 operational hardening — #39, #42, #43

## Security and containers (#39)

The repository runs a scheduled Trivy scan of both built application images plus all infrastructure images. Reports are informational until an operator reviews the OS/package findings, selects supported patched image tags and commits **verified** SHA256 immutable digests. The workflow emits a resolved image-digest inventory artifact; it does not assert that a mutable tag is immutable. Existing pip-audit/npm-audit and fixed-version tag checks remain enforced independently.

**Residual before closing #39:** replace Dockerfile and Compose mutable tag references with independently verified digests for the chosen deployment platform; decide and enforce a high/critical vulnerability policy with documented exemptions and expiry. Do not fabricate digests, and do not close this issue based only on passing report-mode scans.

## Metrics and calculation provenance (#42)

The API emits redacted JSON access records with a server-generated request correlation ID, matched route template, method, status and latency. The new process-local `HttpMetrics` aggregator emits a bounded aggregate per 100 requests: HTTP status class, count, 5xx count, total and maximum latency. It never logs query strings, authorization headers, cookies or raw provider payloads.

`audit_calculation(run_id, version, source, outcome, snapshot_hash)` is an extension point for **server-side** calculation runs and accepts only metadata and a source digest. The present DCF lab evaluates manually entered assumptions in the browser, **not** a server-side source-backed valuation; it therefore does not generate false backend valuation trace events.

**Residual before closing #42:** connect calculation audit events when a persisted source-backed valuation runner exists, and configure central logs/metrics retention, alert routing and exporter in the selected deployment. A process-local counter is not a clustered metrics solution.

## Encrypted backups and recovery (#43)

`scripts/backup_stack.sh` creates a single encrypted age archive containing a consistent PostgreSQL custom-format database dump, an S3-API export of all MinIO buckets/objects and a SHA256 manifest. Set `BACKUP_DIRECTORY` to a filesystem **outside Compose volumes**, `BACKUP_AGE_RECIPIENT` to a previously provisioned public age recipient, and the deployment database and object-storage credentials in the process environment. Install `age` on the host. Do not commit age private identities, encrypted backup archives or object credentials.

`scripts/restore_stack.sh` decrypts and verifies archive hashes and refuses an existing PostgreSQL database. Object recovery always targets *new* prefixed buckets, never overwriting an existing bucket. It requires an age private key at `BACKUP_AGE_IDENTITY`, `BACKUP_FILE`, `RESTORE_DB_NAME` and `RESTORE_BUCKET_PREFIX`.

**Automated drill:** `bash scripts/p2_backup_drill.sh` brings up an isolated Compose project, writes a known MinIO fixture, dumps the PostgreSQL schema and S3 objects, hashes both artifacts, restores PostgreSQL into a distinct database, restores S3 objects into a new prefixed bucket and verifies byte-for-byte equality. It removes only the isolated test project's volumes. The CI scheduled drill repeats this test weekly.

**Threat model and limitations:** age encryption protects the archive on disk, but backups still require secured transfer and managed key recovery. The PostgreSQL dump is consistent by itself; the object archive is a separate point-in-time scan and **not transactionally coordinated** with the database. Applications that depend on cross-store atomicity need quiescence or application-level snapshot coordination. The archive currently preserves content type and object bytes, not all provider-specific S3 version/ACL metadata, bucket policies, object locks or encryption settings. These must be configured separately on restore. Object sizes are capped at 2 GiB per item; larger objects fail closed.

**Remaining deployment acceptance:** implement a real scheduler and external encrypted destination, retention and pruning after verified recovery, separately secured age decryption identities, restore runbook drills against actual hosted data, and document/validate target RPO and RTO. Do not delete unverified old backups. Keep #43 open until these are operationally verified.
