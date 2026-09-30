# FinPilot 1.1.3

Build 5

## Fixes

- Fixed admin billing-plan creation failures when a Google Play product ID is supplied.
- Fixed manual user plan changes, custom-plan clearing, and custom-plan access/status synchronization.
- Restored paise/decimal display across the main finance screens.
- Enabled decimal entry for plan prices, payments, budgets, and savings goals.
- Corrected dashboard total balance so credit-card outstanding is not counted as liquid cash.
- Included credit-card outstanding in liabilities and net-worth calculations.
- Excluded internal account transfers from monthly income/expense, savings-rate, and financial-health calculations.
- Financial health now waits for recorded income instead of producing a misleading score from expense-only data.
- Added regression tests for admin-plan handling and finance calculation accuracy.
