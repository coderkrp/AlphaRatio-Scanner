# Security Policy

## Supported Versions

Currently, only the latest `main` branch and the latest stable release tag are supported with security updates.

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability within AlphaRatio Scanner, please DO NOT open a public issue. We take security seriously and want to address potential exploits (especially those related to local execution, config parsing, or SQL injection vectors) responsibly.

Please email the core maintainer team at `security@example.com` (replace with actual contact in production).

We will attempt to respond to your report within 48 hours. If the vulnerability is accepted, we will create a private patch, publish a security advisory, and credit you for the discovery.

### Threat Model Constraints
Please note that this tool is designed as a *local/private VPS cron job*. It is not currently designed to be exposed to the public internet as a multi-tenant SaaS application. 
- The SQLite database is local.
- The `config.yaml` is local.
Vulnerabilities requiring local machine access to exploit are generally considered outside the threat model, but we still welcome reports on path traversal or arbitrary code execution via YAML parsing.
