# Data Security and Compliance

This document outlines how training data should be handled with respect to
GDPR and HIPAA regulations.

## GDPR Considerations

- Collect only data with explicit user consent and document the purpose of
  processing.
- Apply data minimization so that no unnecessary personal information is
  stored.
- Support the right to access and delete personal data on request.
- Encrypt data at rest and in transit when storing or transferring
  information.
- Maintain records of processing activities and breach‑notification
  procedures.

## HIPAA Considerations

- Treat all protected health information (PHI) as confidential and limit
  access to authorized personnel.
- Use secure authentication and audit logging to track data access.
- Ensure data is encrypted both at rest and during transmission.
- Provide business associate agreements (BAAs) with any third‑party service
  that processes PHI.
- Implement policies for timely breach reporting and incident response.

## Best Practices

- Regularly review datasets for sensitive information before uploading to
  shared storage.
- Rotate credentials for data storage backends and restrict access using
  least‑privilege principles.
- Document data retention periods and remove obsolete records.
