# 🔒 Security Quick Reference

## 🚨 Emergency: I Committed My API Keys!

1. **Revoke keys immediately** at your provider's dashboard
2. **Remove from git**: `git rm --cached keys.py && git commit -m "Remove keys"`
3. **Generate new keys** and update your local keys.py
4. See [SECURITY.md](../SECURITY.md) for history cleanup

## ✅ Quick Setup (New Project)

```bash
# 1. Run security setup
./setup_security.sh  # or setup_security.bat on Windows

# 2. Create keys file
cp keys.example.py keys.py

# 3. Edit with your keys
nano keys.py

# 4. Verify security
python check_security.py
```

## 🔍 Quick Checks

```bash
# Is keys.py ignored?
git check-ignore keys.py  # Should output: keys.py

# Is keys.py tracked?
git ls-files | grep keys.py  # Should output: (nothing)

# Run full security check
python check_security.py
```

## 📝 Files You Should NEVER Commit

- ❌ `keys.py` - Contains actual API keys
- ❌ `.env` - Environment variables
- ❌ `config.local.json` - Local configuration
- ❌ `secrets.json` - Any secrets file
- ❌ `*.key`, `*.pem` - Private keys

## ✅ Files Safe to Commit

- ✅ `keys.example.py` - Template (no real keys)
- ✅ `config.example.json` - Template configuration
- ✅ `.gitignore` - Git ignore rules
- ✅ `SECURITY.md` - Security documentation

## 🛠️ Common Commands

```bash
# Create keys.py from template
cp keys.example.py keys.py

# Install git hooks
./setup_security.sh

# Check security status
python check_security.py

# Verify .gitignore
cat .gitignore | grep keys.py

# Check git history for keys.py
git log --all -- keys.py
```

## 📚 Documentation

- **Full Guide**: [SECURITY.md](../SECURITY.md)
- **Setup Summary**: [SECURITY_SETUP_SUMMARY.md](../SECURITY_SETUP_SUMMARY.md)
- **Main README**: [README.md](../README.md)

## 🔗 Quick Links

- [OpenAI API Keys](https://platform.openai.com/api-keys)
- [DeepSeek API Keys](https://platform.deepseek.com/api_keys)
- [Anthropic API Keys](https://console.anthropic.com/settings/keys)

---

**When in doubt, ask! Security is important! 🔒**
