import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getTicket } from '../api'
import type { Ticket, TicketStatus, Severity } from '../types'
import PayloadViewer from '../components/PayloadViewer'

const POLLING_INTERVAL = 2500
const TERMINAL = new Set<TicketStatus>(['RESOLVED', 'FAILED'])

function StatusBadge({ status }: { status: TicketStatus }) {
  const cls = `badge badge-${status.toLowerCase()}`
  return <span className={cls}>{status}</span>
}

function SeverityBadge({ severity }: { severity: Severity | null }) {
  if (!severity) return null
  return <span className={`badge badge-${severity}`}>{severity}</span>
}

export default function TicketDetail() {
  const { id } = useParams<{ id: string }>()
  const [ticket, setTicket] = useState<Ticket | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!id) return
    let active = true

    async function poll() {
      try {
        const t = await getTicket(id!)
        if (!active) return
        setTicket(t)
        if (!TERMINAL.has(t.status)) {
          setTimeout(poll, POLLING_INTERVAL)
        }
      } catch (err) {
        if (active) setError(String(err))
      }
    }

    poll()
    return () => { active = false }
  }, [id])

  if (error) return (
    <div className="container">
      <Link to="/" className="back">← New ticket</Link>
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
      <Link to="/" className="back">← New ticket</Link>

      <div className="card">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
          <h1 style={{ fontSize: '1.2rem' }}>{ticket.id}</h1>
          <StatusBadge status={ticket.status} />
          <SeverityBadge severity={ticket.severity} />
          {pending && <span className="spinner" />}
        </div>

        {ticket.job_name && <p className="meta">Job: {ticket.job_name}</p>}
        {ticket.build_url && (
          <p className="meta">
            Build: <a href={ticket.build_url} target="_blank" rel="noreferrer">{ticket.build_url}</a>
          </p>
        )}
        <p className="meta">Created: {new Date(ticket.created_at).toLocaleString()}</p>
      </div>

      {ticket.investigation && (
        <div className="card">
          <h2>Investigation</h2>
          <pre className="report">{ticket.investigation}</pre>
        </div>
      )}

      {pending && !ticket.investigation && (
        <div className="card">
          <p style={{ color: '#94a3b8' }}>
            <span className="spinner" />
            {ticket.status === 'OPEN' ? 'Queued…' : 'AI is investigating…'}
          </p>
        </div>
      )}

      {ticket.teams_payload && (
        <PayloadViewer title="Teams payload (mock)" data={ticket.teams_payload} />
      )}
      {ticket.jira_payload && (
        <PayloadViewer title="Jira payload (mock)" data={ticket.jira_payload} />
      )}
      {ticket.wiki_payload && (
        <PayloadViewer title="KB wiki entry (mock)" data={ticket.wiki_payload} />
      )}
    </div>
  )
}
