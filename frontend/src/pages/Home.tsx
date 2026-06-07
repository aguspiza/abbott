import { useState, useEffect, useRef, FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { createTicket, listTickets, addNote } from '../api'
import type { Ticket, TicketStatus, Severity } from '../types'

const POLL_MS = 3000
const TERMINAL = new Set<TicketStatus>(['RESOLVED', 'FAILED'])
const DAY_OPTIONS = [5, 30, 0] as const

function timeAgo(iso: string) {
  const s = Math.floor((Date.now() - new Date(iso).getTime()) / 1000)
  if (s < 60) return `${s}s ago`
  if (s < 3600) return `${Math.floor(s / 60)}m ago`
  if (s < 86400) return `${Math.floor(s / 3600)}h ago`
  return `${Math.floor(s / 86400)}d ago`
}

function StatusBadge({ status }: { status: TicketStatus }) {
  return <span className={`badge badge-${status.toLowerCase()}`}>{status}</span>
}

function SeverityBadge({ severity }: { severity: Severity | null }) {
  if (!severity || severity === 'unknown') return null
  return <span className={`badge badge-${severity}`}>{severity}</span>
}

function TicketRow({ ticket, onUpdated }: { ticket: Ticket; onUpdated: (t: Ticket) => void }) {
  const [expanded, setExpanded] = useState(false)
  const [note, setNote] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function submitNote(e: FormEvent) {
    e.preventDefault()
    if (!note.trim()) return
    setSubmitting(true)
    try {
      const updated = await addNote(ticket.id, note)
      setNote('')
      setExpanded(false)
      onUpdated(updated)
    } finally {
      setSubmitting(false)
    }
  }

  const pending = !TERMINAL.has(ticket.status)

  return (
    <div className="ticket-row">
      <div className="ticket-row-main">
        <div className="ticket-row-left">
          <Link to={`/tickets/${ticket.id}`} className="ticket-id">{ticket.id}</Link>
          <StatusBadge status={ticket.status} />
          <SeverityBadge severity={ticket.severity} />
          {pending && <span className="spinner" style={{ width: '0.75rem', height: '0.75rem' }} />}
        </div>
        <div className="ticket-row-right">
          <span className="meta">{ticket.job_name ?? '—'}</span>
          <span className="meta">{timeAgo(ticket.created_at)}</span>
          <button
            className="btn-ghost"
            onClick={() => setExpanded(e => !e)}
          >
            {expanded ? 'Cancel' : '+ Add context'}
          </button>
        </div>
      </div>

      {expanded && (
        <form className="note-form" onSubmit={submitNote}>
          <textarea
            rows={3}
            placeholder="Add context to help the AI re-investigate… (e.g. recent changes, environment details)"
            value={note}
            onChange={e => setNote(e.target.value)}
            autoFocus
          />
          <button type="submit" disabled={submitting || !note.trim()}>
            {submitting ? 'Submitting…' : 'Re-investigate'}
          </button>
        </form>
      )}
    </div>
  )
}

export default function Home() {
  const [tickets, setTickets] = useState<Ticket[]>([])
  const [days, setDays] = useState<number>(5)
  const [rawLog, setRawLog] = useState('')
  const [buildUrl, setBuildUrl] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  async function refresh(d = days) {
    try {
      const data = await listTickets(d)
      setTickets(data)
    } catch { /* ignore poll errors */ }
  }

  useEffect(() => {
    refresh(days)
    pollRef.current = setInterval(() => refresh(days), POLL_MS)
    return () => { if (pollRef.current) clearInterval(pollRef.current) }
  }, [days])

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!rawLog.trim()) return
    setSubmitting(true)
    setError('')
    try {
      const ticket = await createTicket({
        raw_log: rawLog,
        build_url: buildUrl || undefined,
      })
      setTickets(prev => [ticket, ...prev])
      setRawLog('')
      setBuildUrl('')
    } catch (err) {
      setError(String(err))
    } finally {
      setSubmitting(false)
    }
  }

  function updateTicket(updated: Ticket) {
    setTickets(prev => prev.map(t => t.id === updated.id ? updated : t))
  }

  return (
    <div className="container">
      <div style={{ marginBottom: '1.5rem' }}>
        <h1>Abbott</h1>
        <p className="meta">AI-powered Jenkins pipeline failure investigator</p>
      </div>

      <div className="card">
        <h2>New investigation</h2>
        <form onSubmit={handleSubmit}>
          <label>Jenkins log *</label>
          <textarea
            rows={10}
            placeholder="Paste the full Jenkins console output here…"
            value={rawLog}
            onChange={e => setRawLog(e.target.value)}
            required
          />
          <label>Build URL <span className="meta">(job name extracted automatically)</span></label>
          <input
            type="url"
            placeholder="https://jenkins.example.com/job/my-job/42/"
            value={buildUrl}
            onChange={e => setBuildUrl(e.target.value)}
          />
          {error && <p className="error">{error}</p>}
          <button type="submit" disabled={submitting || !rawLog.trim()}>
            {submitting ? <><span className="spinner" />Submitting…</> : 'Investigate'}
          </button>
        </form>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
        <h2 style={{ margin: 0 }}>Recent tickets</h2>
        <div className="day-filter">
          {DAY_OPTIONS.map(d => (
            <button
              key={d}
              className={`btn-filter ${days === d ? 'active' : ''}`}
              onClick={() => setDays(d)}
            >
              {d === 0 ? 'All' : `${d}d`}
            </button>
          ))}
        </div>
      </div>

      {tickets.length === 0
        ? <p className="meta" style={{ textAlign: 'center', padding: '2rem' }}>No tickets yet.</p>
        : tickets.map(t => (
            <TicketRow key={t.id} ticket={t} onUpdated={updateTicket} />
          ))
      }
    </div>
  )
}
