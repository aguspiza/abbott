import { useState, FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { createTicket } from '../api'

export default function SubmitTicket() {
  const navigate = useNavigate()
  const [rawLog, setRawLog] = useState('')
  const [jobName, setJobName] = useState('')
  const [buildUrl, setBuildUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!rawLog.trim()) return
    setLoading(true)
    setError('')
    try {
      const ticket = await createTicket({
        raw_log: rawLog,
        job_name: jobName || undefined,
        build_url: buildUrl || undefined,
      })
      navigate(`/tickets/${ticket.id}`)
    } catch (err) {
      setError(String(err))
      setLoading(false)
    }
  }

  return (
    <div className="container">
      <h1>Abbott</h1>
      <p className="meta" style={{ marginBottom: '1.5rem' }}>
        AI-powered Jenkins pipeline failure investigator
      </p>

      <div className="card">
        <form onSubmit={handleSubmit}>
          <label>Jenkins log *</label>
          <textarea
            rows={14}
            placeholder="Paste the full Jenkins console output here…"
            value={rawLog}
            onChange={e => setRawLog(e.target.value)}
            required
          />

          <label>Job name</label>
          <input
            type="text"
            placeholder="e.g. build-service"
            value={jobName}
            onChange={e => setJobName(e.target.value)}
          />

          <label>Build URL</label>
          <input
            type="url"
            placeholder="https://jenkins.example.com/job/…"
            value={buildUrl}
            onChange={e => setBuildUrl(e.target.value)}
          />

          {error && <p className="error">{error}</p>}

          <button type="submit" disabled={loading || !rawLog.trim()}>
            {loading ? <><span className="spinner" />Submitting…</> : 'Investigate'}
          </button>
        </form>
      </div>
    </div>
  )
}
