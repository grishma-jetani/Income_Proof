import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import FileDropzone from '../components/FileDropzone'
import { uploadStatements, getCoverage } from '../api/incomeproof'
import { AlertCircle, Info } from 'lucide-react'

export default function UploadPage() {
  const [files, setFiles] = useState([])
  const [error, setError] = useState(null)
  const [isUploading, setIsUploading] = useState(false)
  const [coverageWarning, setCoverageWarning] = useState(null)
  const [coverageData, setCoverageData] = useState([])
  const navigate = useNavigate()

  useEffect(() => {
    getCoverage()
      .then(({ coverage, warning }) => {
        setCoverageData(coverage)
        setCoverageWarning(warning)
      })
      .catch(() => {})
  }, [])

  const handleProcess = async () => {
    if (files.length === 0) return
    setError(null)
    setIsUploading(true)

    try {
      const rawFiles = files.map((f) => f.file)
      const labels = files.map((f) => f.source)
      const uploadResults = await uploadStatements(rawFiles, labels)
      const statementIds = uploadResults.map((r) => r.statement_id)
      navigate('/processing', { state: { statementIds } })
    } catch (err) {
      setError(
        err?.response?.data?.detail ||
          'Upload failed. Make sure the backend is running on port 8000.'
      )
      setIsUploading(false)
    }
  }

  return (
    <div className="flex flex-col gap-6 max-w-3xl">
      <div>
        <h2 className="font-display text-2xl font-semibold text-ink">Upload Statements</h2>
        <p className="text-sm text-slate mt-1">
          Add bank statement PDFs or UPI export CSVs from one or more sources.
        </p>
      </div>

      {/* Existing coverage summary */}
      {coverageData.length > 0 && (
        <div className="bg-white rounded-2xl border border-border shadow-card p-4 flex flex-col gap-3">
          <p className="text-xs font-semibold text-slate uppercase tracking-wide">
            Already uploaded
          </p>
          <div className="flex flex-col gap-1.5">
            {coverageData.map((c) => (
              <div key={c.source_format} className="flex items-center justify-between text-sm">
                <span className="font-medium text-ink">{c.source_label}</span>
                <span className="text-slate">
                  {c.min_date} → {c.max_date}
                  <span className="text-xs ml-2 text-slate/60">({c.transaction_count} txns)</span>
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Smart cross-source overlap warning */}
      {coverageWarning && (
        <div className="flex items-start gap-3 bg-gold/10 border border-gold/40 rounded-2xl p-4">
          <Info size={18} className="text-gold flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-semibold text-ink mb-1">Date range guidance</p>
            <p className="text-sm text-ink/80 leading-relaxed">{coverageWarning}</p>
          </div>
        </div>
      )}

      <FileDropzone files={files} setFiles={setFiles} />

      {error && (
        <div className="flex items-start gap-3 bg-rust/10 border border-rust/30 rounded-2xl p-4">
          <AlertCircle size={18} className="text-rust flex-shrink-0 mt-0.5" />
          <p className="text-sm text-rust">{error}</p>
        </div>
      )}

      <div className="flex justify-end">
        <button
          onClick={handleProcess}
          disabled={files.length === 0 || isUploading}
          className="bg-forest text-cream rounded-xl px-6 py-2.5 text-sm font-medium
                     hover:bg-forest-dark transition-colors
                     disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2"
        >
          {isUploading ? (
            <>
              <span className="w-4 h-4 border-2 border-cream/40 border-t-cream rounded-full animate-spin" />
              Uploading…
            </>
          ) : (
            'Process Statements'
          )}
        </button>
      </div>
    </div>
  )
}