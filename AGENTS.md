# Agent workflow: meta-model use

Use the model as a meta-level tool to understand and improve this repository, not as a source of unverified facts or as a runtime feature. For each task:

1. Restate the requested outcome and identify its scope before changing files.
2. Map the relevant implementation, tests, documentation, and workflow configuration. Treat code and executable tests as evidence of current behavior; distinguish those facts from plans, claims, or conceptual language in documentation.
3. Identify the relevant source of truth and constraints. Trace affected call sites and neighboring behavior instead of inferring behavior from names alone. If evidence is missing or contradictory, state the uncertainty and avoid inventing details.
4. Propose the smallest complete change. Preserve unrelated behavior and repository conventions; update directly affected documentation or tests when appropriate.
5. Validate with existing, relevant checks. Use commands declared by the project and workflows; report what was run and any limitations. Do not claim a check passed unless it actually ran successfully.
6. Review the final diff for scope, correctness, unintended files, and exposed secrets before reporting the result.

For meta-level requests, examine how repository components, policies, tests, and agent workflows interact. Prefer durable instructions or documentation when the requested outcome is workflow guidance; do not add runtime code unless the request requires runtime behavior.
