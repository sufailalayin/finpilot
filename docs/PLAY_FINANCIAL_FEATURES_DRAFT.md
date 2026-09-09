# FinPilot — Google Play Financial Features Declaration Draft

**App:** FinPilot  
**Publisher:** Hastron Ventures  
**Package:** com.hastronventures.finpilot  
**Prepared:** 9 September 2026

> Google requires every app published on Google Play to complete the Financial features declaration, including apps that do not offer financial features. This draft reflects the current FinPilot v1 feature set and should be checked against the final production build before submission.

## Recommended declaration for current FinPilot v1

### Financial advice — YES

FinPilot provides personal-finance guidance and AI-assisted financial insights, including budgeting, goal planning, financial-health indicators, debt/net-worth analysis, cash-flow insights and AI-generated informational responses.

Because Google's declaration includes **Financial advice** as a financial feature, this is the clearest matching category for FinPilot.

Important product disclosure:
- FinPilot provides informational tools and guidance.
- FinPilot does not guarantee financial outcomes.
- AI output is not a substitute for regulated professional advice where such advice is required by law.

### Other — likely YES

FinPilot provides broader personal-finance management functionality that does not neatly fit banking, lending, payments, trading or insurance:
- Account and transaction tracking
- Budgets
- Savings goals
- Bills and recurring commitments
- Net-worth tracking
- Asset/liability tracking
- Financial health scoring

If Play Console allows an explanatory text field for "Other," describe FinPilot as a **personal finance management and financial planning application**.

## Categories FinPilot should NOT select for the current v1 unless functionality changes

- Personal loan direct lender
- Loan facilitator
- Payday loans
- Banking
- Line of credit
- Earned wage advances
- Microfinance banking
- Mobile payments and digital wallets
- Money transfer and wire services
- Buy now, pay later
- Cryptocurrency wallet
- Cryptocurrency exchange
- NFT sales/trading/awards
- Crowdfunding and chit funds
- Insurance

### Stock trading and portfolio management — currently NO

FinPilot can record assets/investments for personal tracking and analysis, but the current v1 does not execute securities trades, hold customer brokerage assets, or operate a brokerage/portfolio-management service.

If a future FinPilot version adds live brokerage connectivity, order execution, discretionary investment management, or portfolio-management services, reassess this declaration before publishing that update.

### Credit monitoring and reporting — currently NO

Do not select this unless FinPilot starts obtaining or reporting formal credit bureau/credit-score information.

## Lending / RBI implications for India

Current FinPilot v1 does **not** offer personal loans, act as a loan facilitator, or connect users to lenders. Therefore the additional Google Play documentation requirements that apply to personal-loan apps in India should not apply to the current product.

Do not introduce loan facilitation, lender lead-generation or personal-loan offers without a separate legal/policy review.

## Suggested Play Console wording

**What does FinPilot do?**

"FinPilot is a personal finance management and planning application. Users manually track accounts, transactions, budgets, goals, bills, assets and liabilities. FinPilot also provides informational financial-health indicators and AI-assisted financial guidance. FinPilot does not provide banking services, execute payments, lend money, facilitate loans, hold customer funds, or execute securities trades."

## Pre-submission check

- [ ] Final production app still does not lend or facilitate lending.
- [ ] Final app still does not execute payments or money transfers.
- [ ] Final app still does not execute securities/crypto trades.
- [ ] Store description matches the declaration.
- [ ] Privacy Policy describes AI-assisted financial guidance.
- [ ] Financial disclaimer is visible where appropriate.
- [ ] Any country-specific regulatory obligations have been reviewed before expanding financial functionality.
