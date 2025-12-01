# Security Policy

## Reporting a Vulnerability

If you discover a security issue, please **do not** open a public issue. Instead, report it privately to ensure responsible disclosure.

### Contact

**Preferred method**: [Open a private security advisory](https://github.com/emre2821/Alter_Ego/security/advisories/new) via GitHub

**Alternative**: Email the maintainer directly (see repository profile for contact information)

Please include:
- Description of the issue and potential impact
- Steps to reproduce
- Any suggested mitigations
- Your contact information for follow-up

## Response Timeline

| Stage | Timeline |
|-------|----------|
| Initial acknowledgment | Within **5 business days** |
| Preliminary assessment | Within **10 business days** |
| Status updates | At least every **2 weeks** |
| Fix release | Depends on severity |

## Supported Versions

| Version | Supported |
|---------|-----------|
| Latest release | ✅ Active support |
| Previous minor | ⚠️ Critical fixes only |
| Older versions | ❌ No support |

## Security Best Practices

When using Alter/Ego:

1. **Keep dependencies updated**: Run `pip install --upgrade alter-ego` regularly
2. **Review environment variables**: Avoid committing `.env` files with sensitive data
3. **Use virtual environments**: Isolate project dependencies
4. **Verify downloads**: Install only from official PyPI or this repository

## Security Scanning

This project uses automated security scanning:
- **Bandit**: Static analysis for Python security issues
- **Dependabot**: Automated dependency vulnerability alerts

## Acknowledgments

We appreciate security researchers who help keep Alter/Ego safe. Contributors who responsibly disclose vulnerabilities will be acknowledged (with permission) in release notes.
