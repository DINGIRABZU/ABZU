# Dependency Graph

Generated with `pipdeptree --packages spiral-os`.

```
spiral-os==0.1.0
├── numpy [required: ==1.26.4, installed: 1.26.4]
├── requests [required: ==2.32.4, installed: 2.32.4]
│   ├── charset-normalizer [required: >=2,<4, installed: 3.4.3]
│   ├── idna [required: >=2.5,<4, installed: 3.10]
│   ├── urllib3 [required: >=1.21.1,<3, installed: 2.5.0]
│   └── certifi [required: >=2017.4.17, installed: 2025.8.3]
├── python-json-logger [required: ==3.3.0, installed: 3.3.0]
├── PyYAML [required: ==6.0.2, installed: 6.0.2]
└── psutil [required: ==7.0.0, installed: 7.0.0]
```

## Security and Licensing Notes

`pip-audit` reported no known vulnerabilities.

Licenses of core dependencies (`pip-licenses`):

- numpy 1.26.4 — BSD License
- requests 2.32.4 — Apache Software License
- python-json-logger 3.3.0 — BSD License
- PyYAML 6.0.2 — MIT license
- psutil 7.0.0 — BSD License

