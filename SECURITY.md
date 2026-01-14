# 🔒 Security Guidelines for DeepEcho

## API Key Security

### ⚠️ Important Security Rules

1. **NEVER commit API keys to version control**
   - The `keys.py` file is already in `.gitignore`
   - Always use `keys.example.py` as a template
   - Never share your actual `keys.py` file

2. **Keep your API keys private**
   - Don't share keys in screenshots
   - Don't post keys in issues or pull requests
   - Don't include keys in documentation

3. **Rotate keys regularly**
   - Change your API keys periodically
   - Immediately rotate if you suspect a key has been exposed
   - Use different keys for development and production

## Configuration Methods (Security Comparison)

### Method 1: Configuration File (config.json)
**Security Level**: ⭐⭐⭐ Medium

✅ Pros:
- Easy to manage multiple configurations
- Can be version controlled (without API keys)
- Supports environment-specific settings

⚠️ Cons:
- API keys stored in plain text
- Need to ensure config.json is in .gitignore if it contains keys

**Best Practice**: Use environment variables for API keys in config.json:
```json
{
  "ai_provider": {
    "api_key": "${DEEPSEEK_API_KEY}"
  }
}
```

### Method 2: Environment Variables
**Security Level**: ⭐⭐⭐⭐ High

✅ Pros:
- Keys never stored in files
- Different keys per environment
- Standard security practice

⚠️ Cons:
- Need to set up for each environment
- Can be forgotten in deployment

**Setup**:
```bash
# Linux/macOS
export DEEPSEEK_API_KEY="your-key-here"
export OPENAI_API_KEY="your-key-here"

# Windows (PowerShell)
$env:DEEPSEEK_API_KEY="your-key-here"
$env:OPENAI_API_KEY="your-key-here"

# Windows (CMD)
set DEEPSEEK_API_KEY=your-key-here
set OPENAI_API_KEY=your-key-here
```

### Method 3: keys.py File
**Security Level**: ⭐⭐⭐ Medium

✅ Pros:
- Simple to set up
- Works immediately
- Already in .gitignore

⚠️ Cons:
- Easy to accidentally commit if .gitignore is misconfigured
- Keys stored in plain text

**Setup**:
```bash
# Copy the template
cp keys.example.py keys.py

# Edit keys.py with your actual keys
# The file is automatically excluded from git
```

## Checking Your Security

### Verify .gitignore Configuration

Run this command to ensure keys.py is ignored:
```bash
git check-ignore keys.py
```

Expected output: `keys.py` (means it's properly ignored)

### Check for Accidentally Committed Keys

```bash
# Check if keys.py is tracked by git
git ls-files | grep keys.py
```

Expected output: (empty - no output means it's not tracked)

### Scan for Exposed Keys in History

```bash
# Search git history for potential key leaks
git log --all --full-history --source --pretty=format:"%h %s" -- keys.py
```

## What to Do If You Exposed a Key

### Immediate Actions:

1. **Revoke the exposed key immediately**
   - OpenAI: https://platform.openai.com/api-keys
   - DeepSeek: https://platform.deepseek.com/api_keys
   - Other providers: Check their respective dashboards

2. **Generate a new key**
   - Create a new API key from your provider's dashboard
   - Update your local configuration

3. **Remove from git history** (if committed):
   ```bash
   # Use git filter-branch or BFG Repo-Cleaner
   # WARNING: This rewrites history
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch keys.py" \
     --prune-empty --tag-name-filter cat -- --all
   
   # Force push (only if necessary and coordinated with team)
   git push origin --force --all
   ```

4. **Notify your team**
   - If working in a team, inform everyone about the incident
   - Ensure everyone updates their local keys

## Best Practices

### For Development

1. **Use separate keys for development and production**
2. **Set up environment variables in your shell profile**:
   ```bash
   # Add to ~/.bashrc or ~/.zshrc
   export DEEPSEEK_API_KEY="dev-key-here"
   ```

3. **Use a password manager** to store API keys securely

### For Production

1. **Use environment variables or secret management services**
   - AWS Secrets Manager
   - Azure Key Vault
   - HashiCorp Vault
   - Google Cloud Secret Manager

2. **Implement key rotation policies**
3. **Monitor API usage for anomalies**
4. **Set up usage limits and alerts**

### For Teams

1. **Document the key management process**
2. **Use a shared secret management tool**
3. **Implement code review for configuration changes**
4. **Set up pre-commit hooks to prevent key commits**:

```bash
# .git/hooks/pre-commit
#!/bin/bash
if git diff --cached --name-only | grep -q "keys.py"; then
    echo "Error: Attempting to commit keys.py"
    echo "This file should never be committed!"
    exit 1
fi
```

## Additional Security Measures

### 1. API Key Restrictions

Configure API key restrictions at the provider level:
- IP address restrictions
- Usage quotas
- Rate limiting
- Allowed endpoints

### 2. Monitoring

Set up monitoring for:
- Unusual API usage patterns
- Failed authentication attempts
- Unexpected geographic access
- Cost anomalies

### 3. Regular Audits

- Review API key usage monthly
- Check for unused or old keys
- Verify access permissions
- Update security policies

## Resources

- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [GitHub Secret Scanning](https://docs.github.com/en/code-security/secret-scanning)
- [Git-secrets Tool](https://github.com/awslabs/git-secrets)

## Reporting Security Issues

If you discover a security vulnerability in DeepEcho:

1. **DO NOT** open a public issue
2. Email the maintainers directly
3. Provide detailed information about the vulnerability
4. Allow time for the issue to be addressed before public disclosure

---

**Remember**: Security is everyone's responsibility. When in doubt, ask for help!
