import { useState, useRef } from 'react'
import { UploadCloud, FileText, X } from 'lucide-react'

const SOURCE_OPTIONS = ['Bank of India', 'PhonePe', 'Other / Unrecognized']

const guessSource = (filename) => {
  const lower = filename.toLowerCase()
  if (lower.includes('boi') || lower.includes('bank')) return 'Bank of India'
  if (lower.includes('phonepe')) return 'PhonePe'
  return 'Other / Unrecognized'
}

export default function FileDropzone({ files, setFiles }) {
  const [isDragging, setIsDragging] = useState(false)
  const inputRef = useRef(null)

  const addFiles = (fileList) => {
    const newFiles = Array.from(fileList).map((file) => ({
      file,
      id: `${file.name}-${file.size}-${Date.now()}-${Math.random()}`,
      source: guessSource(file.name),
    }))
    setFiles((prev) => [...prev, ...newFiles])
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setIsDragging(false)
    addFiles(e.dataTransfer.files)
  }

  const handleSourceChange = (id, value) => {
    setFiles((prev) => prev.map((f) => (f.id === id ? { ...f, source: value } : f)))
  }

  const removeFile = (id) => {
    setFiles((prev) => prev.filter((f) => f.id !== id))
  }

  return (
    <div className="flex flex-col gap-4">
      <div
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={`flex flex-col items-center justify-center gap-3 border-2 border-dashed rounded-2xl py-14 cursor-pointer transition-colors
          ${isDragging ? 'border-forest bg-forest/5' : 'border-border bg-white hover:border-forest/40'}`}
      >
        <div className="w-12 h-12 rounded-full bg-forest/10 flex items-center justify-center">
          <UploadCloud size={22} className="text-forest" />
        </div>
        <div className="text-center">
          <p className="text-sm font-medium text-ink">
            Drag and drop statements here, or click to browse
          </p>
          <p className="text-xs text-slate mt-1">Supports PDF and CSV files from any bank or UPI app</p>
        </div>
        <input
          ref={inputRef}
          type="file"
          multiple
          accept=".pdf,.csv"
          className="hidden"
          onChange={(e) => addFiles(e.target.files)}
        />
      </div>

      {files.length > 0 && (
        <div className="flex flex-col gap-2">
          {files.map(({ file, id, source }) => (
            <div
              key={id}
              className="flex items-center justify-between bg-white rounded-xl border border-border px-4 py-3"
            >
              <div className="flex items-center gap-3 min-w-0">
                <div className="w-9 h-9 rounded-lg bg-gold/15 flex items-center justify-center flex-shrink-0">
                  <FileText size={16} className="text-gold" />
                </div>
                <div className="min-w-0">
                  <p className="text-sm font-medium text-ink truncate">{file.name}</p>
                  <p className="text-xs text-slate">{(file.size / 1024).toFixed(1)} KB</p>
                </div>
              </div>

              <div className="flex items-center gap-3 flex-shrink-0">
                <select
                  value={source}
                  onChange={(e) => handleSourceChange(id, e.target.value)}
                  className="text-xs rounded-lg border border-border px-2 py-1.5 bg-cream
                             focus:outline-none focus:ring-2 focus:ring-forest/30"
                >
                  {SOURCE_OPTIONS.map((opt) => (
                    <option key={opt} value={opt}>{opt}</option>
                  ))}
                </select>
                <button
                  onClick={() => removeFile(id)}
                  className="text-slate hover:text-rust transition-colors"
                >
                  <X size={16} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}