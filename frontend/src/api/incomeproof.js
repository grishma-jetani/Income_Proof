import client from './client'

// Upload one or more statement files
// files: File[] from the dropzone
// sourceLabels: string[] matching files array order
export async function uploadStatements(files, sourceLabels) {
  const formData = new FormData()
  files.forEach((file) => formData.append('files', file))
  formData.append('source_labels', sourceLabels.join(','))

  const res = await client.post('/api/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return res.data // [{ statement_id, filename, status }]
}

// Poll until status is 'done' or 'failed'
export async function getStatementStatus(statementId) {
  const res = await client.get(`/api/statements/${statementId}/status`)
  return res.data
  // { statement_id, status, balance_check_passed, balance_check_details, transaction_count }
}

// Fetch all transactions
export async function getTransactions() {
  const res = await client.get('/api/transactions')
  return res.data
}

// Update a single transaction's category
export async function updateTransactionCategory(txnId, category) {
  const res = await client.patch(`/api/transactions/${txnId}/category`, { category })
  return res.data
}

// Dashboard totals + chart data
export async function getDashboard() {
  const res = await client.get('/api/dashboard')
  return res.data
  // { total_income, total_expenses, net_savings, weekly_trend, category_breakdown, recent_transactions }
}

// Stability score + explanation
export async function getStability() {
  const res = await client.get('/api/stability')
  return res.data
  // { stability_score, mean_weekly_income, cv_pct, trend_pct, explanation, period_start, period_end }
}

// Generate and download the income report PDF
// Returns a Blob
export async function generateReport(startDate, endDate, template) {
  const res = await client.get('/api/report', {
    params: {
      start_date: startDate,
      end_date: endDate,
      template,
    },
    responseType: 'blob',
  })
  return res.data // Blob
}

// Get date-range coverage per source already uploaded by this user
export async function getCoverage() {
  const res = await client.get('/api/statements/coverage')
  return res.data  // { coverage: [...], warning: string | null }
}