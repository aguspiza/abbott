export type TicketStatus = 'OPEN' | 'INVESTIGATING' | 'RESOLVED' | 'FAILED'
export type Severity = 'flaky' | 'warning' | 'bug' | 'unknown'

export interface Ticket {
  id: string
  job_name: string | null
  build_url: string | null
  raw_log: string
  parsed: Record<string, unknown> | null
  status: TicketStatus
  severity: Severity | null
  investigation: string | null
  teams_payload: Record<string, unknown> | null
  jira_payload: Record<string, unknown> | null
  wiki_payload: Record<string, unknown> | null
  created_at: string
  updated_at: string
}
