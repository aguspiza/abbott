import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createTicket, getTicket, listTickets, addNote } from '../api'
import type { Ticket } from '../types'

const MOCK_TICKET: Ticket = {
  id: 'TKT-ABCD1234',
  job_name: 'my-job',
  build_url: null,
  raw_log: 'error',
  parsed: null,
  status: 'OPEN',
  severity: null,
  investigation: null,
  notes: [],
  teams_payload: null,
  jira_payload: null,
  wiki_payload: null,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
}

function mockFetch(data: unknown, status = 200) {
  vi.mocked(fetch).mockResolvedValueOnce({
    ok: status < 400,
    status,
    statusText: status < 400 ? 'OK' : 'Error',
    json: async () => data,
  } as Response)
}

beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn())
})

describe('createTicket', () => {
  it('POSTs to /api/tickets and returns the ticket', async () => {
    mockFetch(MOCK_TICKET, 201)
    const result = await createTicket({ raw_log: 'error' })
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/tickets'),
      expect.objectContaining({ method: 'POST' }),
    )
    expect(result.id).toBe('TKT-ABCD1234')
    expect(result.status).toBe('OPEN')
  })

  it('throws on non-ok response', async () => {
    mockFetch({}, 500)
    await expect(createTicket({ raw_log: '' })).rejects.toThrow()
  })

  it('includes build_url in request body when provided', async () => {
    mockFetch(MOCK_TICKET, 201)
    await createTicket({ raw_log: 'err', build_url: 'https://jenkins/job/x/1/' })
    const body = JSON.parse((vi.mocked(fetch).mock.calls[0][1] as RequestInit).body as string)
    expect(body.build_url).toBe('https://jenkins/job/x/1/')
  })
})

describe('getTicket', () => {
  it('GETs /api/tickets/:id', async () => {
    mockFetch(MOCK_TICKET)
    const result = await getTicket('TKT-ABCD1234')
    expect(fetch).toHaveBeenCalledWith(expect.stringContaining('/api/tickets/TKT-ABCD1234'))
    expect(result.id).toBe('TKT-ABCD1234')
  })

  it('throws on 404', async () => {
    mockFetch({ detail: 'Ticket not found' }, 404)
    await expect(getTicket('TKT-NOTREAL')).rejects.toThrow()
  })
})

describe('listTickets', () => {
  it('GETs /api/tickets with default days=5', async () => {
    mockFetch([MOCK_TICKET])
    const results = await listTickets()
    expect(fetch).toHaveBeenCalledWith(expect.stringContaining('days=5'))
    expect(results).toHaveLength(1)
  })

  it('passes custom days param', async () => {
    mockFetch([])
    await listTickets(30)
    expect(fetch).toHaveBeenCalledWith(expect.stringContaining('days=30'))
  })
})

describe('addNote', () => {
  it('POSTs note and returns updated ticket', async () => {
    const updated = { ...MOCK_TICKET, notes: ['Check disk space'], status: 'OPEN' as const }
    mockFetch(updated)
    const result = await addNote('TKT-ABCD1234', 'Check disk space')
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/TKT-ABCD1234/notes'),
      expect.objectContaining({ method: 'POST' }),
    )
    expect(result.notes).toContain('Check disk space')
  })
})
