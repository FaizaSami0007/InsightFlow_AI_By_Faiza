# Data Quality & Contracts

## Quality dimensions

- completeness
- uniqueness
- validity
- consistency
- timeliness
- integrity

## Quality score

A score is a diagnostic summary, not a truth claim. Always show the component checks that produced it.

## Contract violations

Examples:
- numeric column contains invalid tokens
- date parsing failure exceeds threshold
- required field is missing
- duplicate key exceeds configured threshold

## User experience

Do not simply show "Data quality: 72%". Show the causes and provide actionable remediation guidance.
