# Havenline Change Requests

Builders must not modify protected or foreign-owned production paths. Create a JSON request here instead.

Required fields:
```json
{
  "request_id":"CR-TNN-0001",
  "requesting_task":"TNN",
  "target_path":"path/to/file",
  "requested_change":"precise requested edit/interface",
  "reason":"why the requesting task needs it",
  "dependency":"task/interface or null",
  "expected_behavior":"observable result",
  "tests_required":["test or gate"],
  "status":"OPEN",
  "integration_owner_disposition":null
}
```

Only the integration owner may approve/reject/implement a cross-owned production change. Requests are evidence, not authorization by themselves.
