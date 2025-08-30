# Dependency Registry

Approved runtimes and libraries with minimum and approved versions.
Track CVE monitoring links to ensure timely vulnerability remediation. Update this registry when dependencies change and validate updates with `pre-commit run --files docs/dependency_registry.md docs/INDEX.md`.

| Name | Minimum Version | Approved Version | CVE Monitor | Notes |
| --- | --- | --- | --- | --- |
| Python | 3.10 | 3.10 | [NVD](https://nvd.nist.gov/vuln/search/results?query=python) | Primary runtime |
| Node.js | 20 | 20 | [NVD](https://nvd.nist.gov/vuln/search/results?query=node.js) | Web asset pipeline |
| numpy | 2.2.6 | 2.2.6 | [OSV](https://osv.dev/list?ecosystem=PyPI&q=numpy) | Numerical computations |
| opencv-python | 4.12.0.88 | 4.12.0.88 | [OSV](https://osv.dev/list?ecosystem=PyPI&q=opencv-python) | Computer vision operations |
| requests | 2.32.4 | 2.32.4 | [OSV](https://osv.dev/list?ecosystem=PyPI&q=requests) | HTTP client |
| prometheus-client | 0.20.0 | 0.20.0 | [OSV](https://osv.dev/list?ecosystem=PyPI&q=prometheus-client) | Metrics export |
| prometheus-fastapi-instrumentator | 6.1.0 | 6.1.0 | [OSV](https://osv.dev/list?ecosystem=PyPI&q=prometheus-fastapi-instrumentator) | FastAPI metrics middleware |
| psutil | 7.0.0 | 7.0.0 | [OSV](https://osv.dev/list?ecosystem=PyPI&q=psutil) | System resource metrics |
| python-json-logger | 3.3.0 | 3.3.0 | [OSV](https://osv.dev/list?ecosystem=PyPI&q=python-json-logger) | Structured logging |
| pyyaml | 6.0.2 | 6.0.2 | [OSV](https://osv.dev/list?ecosystem=PyPI&q=pyyaml) | YAML parsing |
| scipy | 1.16.1 | 1.16.1 | [OSV](https://osv.dev/list?ecosystem=PyPI&q=scipy) | Scientific computing |
| scikit-learn | 1.7.1 | 1.7.1 | [OSV](https://osv.dev/list?ecosystem=PyPI&q=scikit-learn) | Machine learning utilities |
| soundfile | 0.13.1 | 0.13.1 | [OSV](https://osv.dev/list?ecosystem=PyPI&q=soundfile) | Audio processing |
| phonemizer | 3.3.0 | 3.3.0 | [OSV](https://osv.dev/list?ecosystem=PyPI&q=phonemizer) | Phoneme extraction |
| fastapi | 0.116.1 | 0.116.1 | [OSV](https://osv.dev/list?ecosystem=PyPI&q=fastapi) | Web framework |
| redis | 5.0.3 | 5.0.3 | [OSV](https://osv.dev/list?ecosystem=PyPI&q=redis) | Event processing (optional) |
| aiokafka | 0.10.0 | 0.10.0 | [OSV](https://osv.dev/list?ecosystem=PyPI&q=aiokafka) | Kafka client (optional) |
| asyncpg | 0.29.0 | 0.29.0 | [OSV](https://osv.dev/list?ecosystem=PyPI&q=asyncpg) | PostgreSQL driver (optional) |
| neo4j | 5.23.1 | 5.23.1 | [OSV](https://osv.dev/list?ecosystem=PyPI&q=neo4j) | Graph database client (optional) |
| python-socketio | 5.13.0 | 5.13.0 | [OSV](https://osv.dev/list?ecosystem=PyPI&q=python-socketio) | WebSocket support (optional) |
| vanna | 0.7.9 | 0.7.9 | [OSV](https://osv.dev/list?ecosystem=PyPI&q=vanna) | NLQ queries (optional) |
