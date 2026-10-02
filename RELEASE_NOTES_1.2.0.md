# FinPilot 1.2.0

Build 8

## Highlights

- **Compact Account Cards**: Completely redesigned the dashboard accounts section into compact, touch-friendly rounded candy-chip cards showing individual account names (e.g., Cash, HDFC Bank, SBI), account badges, and clean balance/due indicators.
- **Outside Transfers**: Added support for transfers to and from external parties / outside accounts with directional accounting, notes, and full historical tracking.
- **Instant Plan Synchronization**: Pro feature gating now reacts immediately to server plan updates without requiring app restart.
- **Financial Calculation Integrity**: Comprehensive audit ensuring decimal precision, safe balance tracking, non-inflationary internal transfers, and deterministic financial health scoring.

## Fixes & Enhancements

- Prevented deletion of accounts with linked loan or receivable movements to preserve financial provenance.
- Aligned budget category and recurring rule constraints for complete accounting consistency.
- Enforced strict server-side authorization separating customer and administrator surfaces.
