# Havenline production change requests

Builders do not edit foreign-owned or integration-only production paths.

Copy `CHANGE_REQUEST_TEMPLATE.json` to a uniquely named JSON file and fill every
field. `status` starts `PENDING`. Only the integration owner may set
`status: APPROVED` together with `integration_owner_disposition: AUTHORIZED`.
Authorization is path-specific and does not approve the requesting task.
