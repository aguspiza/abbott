import type { Ticket } from './types'

export async function createTicket(data: {
  raw_log: string
  job_name?: string
  build_url?: string
}): Promise<Ticket> {
  const res = await fetch('/tickets', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json()
}

export async function addNote(id: string, note: string): Promise<Ticket> {
  const res = await fetch(`/tickets/${id}/notes`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ note }),
  })
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json()
}

export async function getTicket(id: string): Promise<Ticket> {
  const res = await fetch(`/tickets/${id}`)
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json()
}

export async function listTickets(days = 5): Promise<Ticket[]> {
  const res = await fetch(`/tickets?days=${days}`)
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json()
}
