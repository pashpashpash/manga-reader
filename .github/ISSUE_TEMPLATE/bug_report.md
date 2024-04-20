---
name: Bug report
about: Create a report to help us improve
title: "BUG: "
labels: bug
assignees: rishi23root
---

**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:

1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected behavior**
A clear and concise description of what you expected to happen.

**Screenshots**
If applicable, add screenshots to help explain your problem.

**Desktop (please complete the following information):**

- OS: [e.g. iOS]
- Browser [e.g. chrome, safari]
- Version [e.g. 22]

> use this command to get the details (for bash shell)

```bash
echo "- OS: $(uname)"
echo "- Browser: $(xdg-settings get default-web-browser)"
echo "- Version: $(
eval "$(xdg-settings get default-web-browser | cut -d'.' -f1 | xargs -I {} which {}) --version"
)"
```

**Smartphone (please complete the following information):**

- Device: [e.g. iPhone6]
- OS: [e.g. iOS8.1]
- Browser [e.g. stock browser, safari]
- Version [e.g. 22]

**Additional context**
Add any other context about the problem here.
