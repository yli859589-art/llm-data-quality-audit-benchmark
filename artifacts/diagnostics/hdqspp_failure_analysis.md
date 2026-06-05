# HDQS++ Failure Analysis

- HDQS++ keep rate: `0.599`
- HDQS++ v2 keep rate: `0.851`
- Token JS HDQS++ vs raw: `0.036954`
- Token JS HDQS++ v2 vs raw: `0.010112`
- Length JS HDQS++ vs raw: `0.034820`
- Length JS HDQS++ v2 vs raw: `0.003600`

Diagnosis: v1 is a hard 60% filter and shifts length/token distribution. v2 is designed to preserve distribution and reduce over-penalization.
