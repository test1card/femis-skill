# Security Policy

`femis` is an Agent Skill and documentation/tooling repository. It does not run a network service, but it does ship
instructions and small Python utilities that may be used around engineering models and solver output.

## Supported Versions

Security fixes are made on the default branch and released from the latest tag.

| Version | Supported |
|---|---|
| latest `main` / latest tag | yes |
| older tags | best effort |

## Reporting a Vulnerability

Do not open a public issue for a vulnerability that could expose credentials, proprietary model data, or unsafe
automation behavior.

Report privately through GitHub's private vulnerability reporting if it is available for this repository, or email
the repository owner listed on GitHub. Include:

- affected file or workflow
- how an agent or user could trigger the problem
- whether credentials, proprietary paths, solver output, or unsafe commands are involved
- a minimal reproduction that does not include proprietary geometry or data

## Scope

Relevant reports include:

- instructions that could cause an agent to run unsafe shell commands or destructive solver workflows
- accidental credential, host, license-server, or proprietary path leakage
- dependency or packaging issues in the helper scripts
- misleading guidance that could cause an agent to present unverified engineering results as sign-off evidence

Engineering disagreements, missing coverage, and ordinary documentation corrections should be opened as normal issues.
