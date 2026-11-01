# Contributing

Thanks for helping improve Recon Lite.

## Development setup

Python 3.10+ is required. The current implementation uses only the standard library.

```powershell
py -3 -m unittest discover -s tests -v
py -3 -m recon_lite samples/headers-example.txt
py -3 -m recon_lite samples/headers-example.txt --format json
```

## Contribution guidelines

- Keep analysis offline and deterministic.
- Add tests for parser behavior and every new finding.
- Explain context and limitations; do not describe the heuristic score as a security grade.
- Avoid collecting or logging supplied header values beyond the requested report.
- Do not add network requests, exploit behavior, credential collection, or telemetry.
- Keep sample data synthetic.

## Pull request checklist

- [ ] Tests pass locally.
- [ ] New behavior has tests.
- [ ] Documentation explains limitations.
- [ ] No secrets, personal data, or real customer headers are included.
