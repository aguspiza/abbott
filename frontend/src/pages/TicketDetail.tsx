import { useEffect, useState, FormEvent } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getTicket, addNote } from '../api'
import type { Ticket, TicketStatus, Severity } from '../types'
import PayloadViewer from '../components/PayloadViewer'

const POLL_MS = 2500
const TERMINAL = new Set<TicketStatus>(['RESOLVED', 'FAILED'])

function StatusBadge({ status }: { status: TicketStatus }) {
  return <span className={`badge badge-${status.toLowerCase()}`}>{status}</span>
}

function SeverityBadge({ severity }: { severity: Severity | null }) {
  if (!severity) return null
  return <span className={`badge badge-${severity}`}>{severity}</span>
}

export default function TicketDetail() {
  const { id } = useParams<{ id: string }>()
  const [ticket, setTicket] = useState<Ticket | null>(null)
  const [error, setError] = useState('')
  const [note, setNote] = useState('')
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    if (!id) return
    let active = true

    async function poll() {
      try {
        const t = await getTicket(id!)
        if (!active) return
        setTicket(t)
        if (!TERMINAL.has(t.status)) setTimeout(poll, POLL_MS)
      } catch (err) {
        if (active) setError(String(err))
      }
    }

    poll()
    return () => { active = false }
  }, [id])

  async function submitNote(e: FormEvent) {
    e.preventDefault()
    if (!note.trim() || !ticket) return
    setSubmitting(true)
    try {
      const updated = await addNote(ticket.id, note)
      setNote('')
      setTicket(updated)
      // restart polling
      const poll = async () => {
        const t = await getTicket(ticket.id)
        setTicket(t)
        if (!TERMINAL.has(t.status)) setTimeout(poll, POLL_MS)
      }
      setTimeout(poll, POLL_MS)
    } finally {
      setSubmitting(false)
    }
  }

  if (error) return (
    <div className="container">
      <Link to="/" className="back">← Back</Link>
      <p className="error">{error}</p>
    </div>
  )

  if (!ticket) return (
    <div className="container">
      <span className="spinner" /> Loading…
    </div>
  )

  const pending = !TERMINAL.has(ticket.status)

  return (
    <div className="container">
      <Link to="/" className="back">← Back</Link>

      <div className="card">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem', flexWrap: 'wrap' }}>
          <h1 style={{ fontSize: '1.2rem' }}>{ticket.id}</h1>
          <StatusBadge status={ticket.status} />
          <SeverityBadge severity={ticket.severity} />
          {pending && <span className="spinner" />}
        </div>
        {ticket.job_name && <p className="meta">Job: {ticket.job_name}</p>}
        {ticket.build_url && (
          <p className="meta">Build: <a href={ticket.build_url} target="_blank" rel="noreferrer">{ticket.build_url}</a></p>
        )}
        <p className="meta">Created: {new Date(ticket.created_at).toLocaleString()}</p>
      </div>

      {ticket.notes.length > 0 && (
        <div className="card">
          <h2>User context</h2>
          <ul style={{ paddingLeft: '1.2rem', lineHeight: 1.8 }}>
            {ticket.notes.map((n, i) => <li key={i} style={{ color: '#cbd5e1', fontSize: '0.9rem' }}>{n}</li>)}
          </ul>
        </div>
      )}

      {ticket.investigation
        ? (
          <div className="card">
            <h2>Investigation {ticket.notes.length > 0 ? `(re-run #${ticket.notes.length})` : ''}</h2>
            <pre className="report">{ticket.investigation}</pre>
          </div>
        )
        : pending && (
          <div className="card">
            <p style={{ color: '#94a3b8' }}>
              <span className="spinner" />
              {ticket.status === 'OPEN' ? 'Queued…' : 'AI is investigating…'}
            </p>
          </div>
        )
      }

      <div className="card">
        <h2>Add context</h2>
        <form onSubmit={submitNote}>
          <textarea
            rows={3}
            placeholder="Provide additional context to re-run the investigation… (recent deployments, config changes, etc.)"
            value={note}
            onChange={e => setNote(e.target.value)}
          />
          <button type="submit" disabled={submitting || !note.trim() || pending}>
            {submitting ? 'Submitting…' : pending ? 'Wait for current run…' : 'Re-investigate'}
          </button>
        </form>
      </div>

      {ticket.teams_payload && <PayloadViewer title="Teams payload (mock)" data={ticket.teams_payload} />}
      {ticket.jira_payload  && <PayloadViewer title="Jira payload (mock)"  data={ticket.jira_payload} />}
      {ticket.wiki_payload  && <PayloadViewer title="KB wiki entry"         data={ticket.wiki_payload} />}
    </div>
  )
}
