export const mockStability = {
  score: 78,
  meanWeeklyIncome: 4250,
  variancePct: 18,
  explanation:
    "Your income has averaged ₹4,250 per week over the last 4 months, with moderate week-to-week variation (±18%). " +
    "Earnings show a gradual upward trend, driven mainly by consistent weekend payouts from Swiggy and Uber. " +
    "A score above 70 suggests income that, while irregular, follows a fairly predictable weekly pattern — " +
    "useful context for lenders evaluating non-salaried applicants.",
}

export const mockTotals = {
  totalIncome: 68800,
  totalExpenses: 41250,
  netSavings: 27550,
}

export const mockIncomeTrend = [
  { week: 'Wk 1', income: 3800, expenses: 2100 },
  { week: 'Wk 2', income: 4200, expenses: 2300 },
  { week: 'Wk 3', income: 3950, expenses: 2050 },
  { week: 'Wk 4', income: 4600, expenses: 2900 },
  { week: 'Wk 5', income: 4100, expenses: 2200 },
  { week: 'Wk 6', income: 4750, expenses: 2600 },
  { week: 'Wk 7', income: 3700, expenses: 2050 },
  { week: 'Wk 8', income: 4900, expenses: 3100 },
  { week: 'Wk 9', income: 4300, expenses: 2400 },
  { week: 'Wk 10', income: 5100, expenses: 2700 },
  { week: 'Wk 11', income: 4450, expenses: 2350 },
  { week: 'Wk 12', income: 4950, expenses: 2900 },
  { week: 'Wk 13', income: 4600, expenses: 2500 },
  { week: 'Wk 14', income: 5300, expenses: 3000 },
  { week: 'Wk 15', income: 4800, expenses: 2650 },
  { week: 'Wk 16', income: 5250, expenses: 2950 },
]

export const mockCategoryBreakdown = [
  { name: 'Swiggy Payouts', value: 62, color: '#2D4A43' },
  { name: 'Rent', value: 14, color: '#C2654A' },
  { name: 'Groceries & Food', value: 10, color: '#C8A560' },
  { name: 'Transfers to Family', value: 8, color: '#5B8A72' },
  { name: 'Utilities & EMI', value: 6, color: '#9CA3AF' },
]

export const mockRecentTransactions = [
  { date: '2026-04-28', description: 'UPI-SWIGGYPAYOUT-558213', category: 'Swiggy Payouts', amount: 720, type: 'credit' },
  { date: '2026-04-27', description: 'UPI-RENT-TRANSFER-TO-LANDLORD-330812', category: 'Rent', amount: 7500, type: 'debit' },
  { date: '2026-04-26', description: 'UPI-UBEREARNINGS-441208', category: 'Uber Earnings', amount: 1180, type: 'credit' },
  { date: '2026-04-25', description: 'UPI-GROCERY-PAYMENT-998123', category: 'Groceries & Food', amount: 640, type: 'debit' },
  { date: '2026-04-24', description: 'UPI-ZOMATOSETTLEMENT-118822', category: 'Zomato Payout', amount: 540, type: 'credit' },
]

export const categoryOptions = [
  // Platform payouts — specific
  'Swiggy Payout',
  'Zomato Payout',
  'Uber Earnings',
  'Ola Earnings',
  'Urban Company Payout',
  'Rapido Earnings',
  'Dunzo Payout',
  'Zepto Payout',
  'Blinkit Payout',
  'Porter Payout',
  // Other income
  'Salary',
  // Expenses
  'Rent',
  'Groceries & Food',
  'Utilities & EMI',
  'Loan EMI',
  'Transfers to Family',
  'Cash Withdrawal',
  'Personal / Other',
]

// Row 8 (id: 8) intentionally mirrors the Stage-1 tamper script:
// original credit ~720, tampered to +8500 -> 9220, balance untouched.
export const mockTransactionsFull = [
  { id: 1, date: '2026-01-03', description: 'UPI-SWIGGYPAYOUT-558213', source: 'Bank of India', category: 'Swiggy Payout', credit: 620, debit: 0 },
  { id: 2, date: '2026-01-04', description: 'UPI-RENT-TRANSFER-TO-LANDLORD-330812', source: 'Bank of India', category: 'Rent', credit: 0, debit: 7500 },
  { id: 3, date: '2026-01-05', description: 'UPI-UBEREARNINGS-441208', source: 'PhonePe', category: 'Uber Earnings', credit: 1180, debit: 0 },
  { id: 4, date: '2026-01-06', description: 'UPI-GROCERY-PAYMENT-998123', source: 'PhonePe', category: 'Groceries & Food', credit: 0, debit: 640 },
  { id: 5, date: '2026-01-07', description: 'UPI-ZOMATOSETTLEMENT-118822', source: 'Bank of India', category: 'Zomato Payout', credit: 540, debit: 0 },
  { id: 6, date: '2026-01-08', description: 'UPI-OLADRIVERPAYOUT-220194', source: 'Bank of India', category: 'OLA Driver Payout', credit: 890, debit: 0 },
  { id: 7, date: '2026-01-09', description: 'UPI-MOBILE-RECHARGE-JIO-110823', source: 'PhonePe', category: 'Utilities & EMI', credit: 0, debit: 299 },
  { id: 8, date: '2026-01-10', description: 'UPI-SWIGGYPAYOUT-771029', source: 'Bank of India', category: 'Swiggy Payout', credit: 9220, debit: 0, flagged: true },
  { id: 9, date: '2026-01-11', description: 'UPI-BIKE-LOAN-EMI-552310', source: 'Bank of India', category: 'Loan EMI', credit: 0, debit: 2500 },
  { id: 10, date: '2026-01-12', description: 'UPI-FOOD-ORDER-PERSONAL-440112', source: 'PhonePe', category: 'Personal / Other', credit: 0, debit: 320 },
  { id: 11, date: '2026-01-13', description: 'UPI-URBANCOMPANYSETTLEMENT-660291', source: 'Bank of India', category: 'Swiggy Payout', credit: 1450, debit: 0 },
  { id: 12, date: '2026-01-14', description: 'UPI-TRANSFER-TO-FAMILY-228810', source: 'Bank of India', category: 'Transfers to Family', credit: 0, debit: 3000 },
  { id: 13, date: '2026-01-15', description: 'UPI-UBEREARNINGS-552093', source: 'PhonePe', category: 'Uber Earnings', credit: 1050, debit: 0 },
  { id: 14, date: '2026-01-16', description: 'UPI-ELECTRICITY-BILL-PAYMENT-771209', source: 'Bank of India', category: 'Utilities & EMI', credit: 0, debit: 840 },
  { id: 15, date: '2026-01-17', description: 'UPI-ZOMATOSETTLEMENT-991002', source: 'Bank of India', category: 'Zomato Payout', credit: 610, debit: 0 },
]
