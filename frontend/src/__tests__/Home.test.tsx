import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import Home from '../pages/Home'
import * as api from '../api'
import type { Ticket } from '../types'

vi.mock('../api')

const MOCK_TICKET: Ticket = {
  id: 'TKT-ABCD1234',
  job_name: 'my-job',
  build_url: null,
  raw_log: 'error',
  parsed: null,
  status: 'RESOLVED',
  severity: 'bug',
  investigation: '## Summary\nBuild failed.',
  notes: [],
  teams_payload: null,
  jira_payload: null,
  wiki_payload: null,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
}

function renderHome() {
  return render(<MemoryRouter><Home /></MemoryRouter>)
}

beforeEach(() => {
  vi.mocked(api.listTickets).mockResolvedValue([])
  vi.mocked(api.createTicket).mockResolvedValue(MOCK_TICKET)
  vi.mocked(api.addNote).mockResolvedValue(MOCK_TICKET)
})

describe('Home', () => {
  it('renders the submit form', () => {
    renderHome()
    expect(screen.getByRole('button', { name: /investigate/i })).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/paste the full jenkins/i)).toBeInTheDocument()
  })

  it('shows empty state when no tickets', async () => {
    renderHome()
    await waitFor(() => {
      expect(screen.getByText(/no tickets yet/i)).toBeInTheDocument()
    })
  })

  it('displays tickets returned from API', async () => {
    vi.mocked(api.listTickets).mockResolvedValue([MOCK_TICKET])
    renderHome()
    await waitFor(() => {
      expect(screen.getByText('TKT-ABCD1234')).toBeInTheDocument()
    })
  })

  it('submits a new ticket and adds it to the list', async () => {
    const user = userEvent.setup()
    renderHome()

    const textarea = screen.getByPlaceholderText(/paste the full jenkins/i)
    await user.type(textarea, 'Build failed with exit code 1')

    const button = screen.getByRole('button', { name: /investigate/i })
    await user.click(button)

    await waitFor(() => {
      expect(api.createTicket).toHaveBeenCalledWith(
        expect.objectContaining({ raw_log: 'Build failed with exit code 1' }),
      )
    })

    expect(screen.getByText('TKT-ABCD1234')).toBeInTheDocument()
  })

  it('submit button is disabled when log textarea is empty', () => {
    renderHome()
    expect(screen.getByRole('button', { name: /investigate/i })).toBeDisabled()
  })

  it('shows error message when createTicket fails', async () => {
    vi.mocked(api.createTicket).mockRejectedValue(new Error('Network error'))
    const user = userEvent.setup()
    renderHome()

    await user.type(screen.getByPlaceholderText(/paste the full jenkins/i), 'some log')
    await user.click(screen.getByRole('button', { name: /investigate/i }))

    await waitFor(() => {
      expect(screen.getByText(/network error/i)).toBeInTheDocument()
    })
  })
})
