# Security Policy

## Supported Versions

We release patches for security vulnerabilities in the following versions:

| Version | Supported          |
| ------- | ------------------ |
| main    | :white_check_mark: |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

If you discover a security vulnerability, please send an email to the repository owner or use GitHub's private vulnerability reporting feature.

Please include the following information:

- Type of vulnerability
- Full paths of source file(s) related to the vulnerability
- Location of the affected source code (tag/branch/commit or direct URL)
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue

## Security Considerations

AWSF requires AWS credentials to function. Please ensure:

1. **Never commit AWS credentials** to version control
2. Use **IAM roles** with least-privilege permissions
3. Regularly **rotate access keys**
4. Use **AWS profiles** instead of hardcoded credentials
5. Review the **IAM permissions** listed in the README

## AWS Credentials

AWSF uses boto3, which follows the AWS credential provider chain:

1. Environment variables
2. AWS credentials file (~/.aws/credentials)
3. IAM role (if running on EC2)

The tool **never stores or transmits** your AWS credentials. All AWS API calls are made locally using boto3.

## Data Privacy

- Resource data is cached locally in `data/aws_resources.json`
- No data is sent to external servers
- All AWS Console URLs are generated client-side
- Configuration is stored locally in `config/`
