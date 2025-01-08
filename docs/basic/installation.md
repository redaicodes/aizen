# Installation

## 1. Basic Installation

```bash
pip install aizen
```

This installs the **core** Aizen library along with all essential dependencies using the published package on PyPI.

---

## 2. Development Installation (Editable Mode)

For contributing or making local modifications to the source code, you can install it directly from the repository using the `pyproject.toml` file:

```bash
pip install -e .
```

This installs the package in editable mode, ensuring changes made to the code reflect immediately in your environment.

---

## 3. Verifying the Installation

You can test your installation by running a simple Python script:

```python
from aizen.agents.base import BaseAgent

agent = BaseAgent()
print("Aizen is ready to go!")
```

---

## 4. Uninstalling

To remove **Aizen** from your system, use:

```bash
pip uninstall aizen
```

---

## 5. Getting Help

If you face any issues during installation or usage, check the [documentation](https://github.com/redaicodes/aizen) or raise an issue on the [GitHub repository](https://github.com/redaicodes/aizen/issues).

---