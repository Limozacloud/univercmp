# univercmp

[![CI](https://github.com/Limozacloud/univercmp/actions/workflows/ci.yml/badge.svg)](https://github.com/Limozacloud/univercmp/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/Limozacloud/univercmp)](LICENSE)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/Limozacloud/univercmp/main?filepath=demo.ipynb)

Cross-platform package version comparison for **APK**, **DEB**, **RPM**, **SemVer** and **PEP 440** ecosystems.

## Installation

```bash
pip install univercmp
```

## Usage

### Library

```python
from univercmp import compare, validate, PackageType

# Compare two versions
result = compare("1.0.0-alpha", "1.0.0", kind=PackageType.SEMVER)
result.verdict   # "older"
result.order     # -1
result.older     # True

# String kind also works
compare("1:1.0-1", "1:1.0-2", kind="deb").older   # True

# Validate a version string
validate("1.0_rc1", kind="apk")    # True
validate("not-valid", kind="deb")  # False

# Direct submodule access (no validation wrapper)
from univercmp.rpm import compare as rpm_cmp
rpm_cmp("4.18.0-513.24.1.el8_9", "4.18.0-553.el8_10")  # -1

from univercmp.semver import parse
sv = parse("1.2.3-alpha.1+build.42")
sv.major  # 1
sv.pre    # ("alpha", "1")
```

### CLI

```bash
# Compare two versions
univercmp compare 1.0.0-alpha 1.0.0 --type semver
# 1.0.0-alpha  <  1.0.0  (older)

univercmp compare 1.0 1.1 --type rpm --quiet
# -1

# Validate a version string
univercmp validate 1.0_rc1 --type apk   # exit 0
univercmp validate 1.0_foo --type apk   # exit 1
```

## Supported ecosystems

| Kind     | Ecosystem                                            | Spec |
|----------|------------------------------------------------------|------|
| `apk`    | Alpine Linux (apk-tools)                             | apk-tools man page |
| `deb`    | Debian, Ubuntu (dpkg)                                | [deb-version(5)](https://manpages.debian.org/deb-version.5) |
| `rpm`    | RHEL, AlmaLinux, Rocky Linux, CentOS, SLES, openSUSE | RPM NEVRA spec |
| `semver` | Any project following Semantic Versioning            | [semver.org](https://semver.org/) |
| `pep440` | Python packages (PyPI, pip)                          | [PEP 440](https://peps.python.org/pep-0440/) |

## License

MIT
