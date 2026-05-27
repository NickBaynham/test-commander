# Glossary

Universal SaaS terms used throughout the sample-project corpus.

Account
: A registered user of the platform. Identified by an opaque account identifier and a display name. May hold the `member` or `admin` role.

Session
: A short-lived authenticated context bound to a single account. Created by the sign-in endpoint and destroyed by sign-out.

Workspace
: A named container owned by an account. Holds a collection of assets and a per-account permission list.

Asset
: A binary file uploaded into a workspace. Carries a content type and a size in bytes.

Permission
: The relation between an account and a workspace. Carries one of `read`, `write`, or `admin`.
