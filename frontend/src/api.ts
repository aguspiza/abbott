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

export async function getTicket(id: string): Promise<Ticket> {
  const res = await fetch(`/tickets/${id}`)
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json()
}

export async function listTickets(): Promise<Ticket[]> {
  const res = await fetch('/tickets')
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json()
}
