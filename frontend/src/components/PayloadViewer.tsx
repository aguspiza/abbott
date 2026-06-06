interface Props {
  title: string
  data: Record<string, unknown>
}

export default function PayloadViewer({ title, data }: Props) {
  return (
    <div className="card">
      <h2>{title}</h2>
      <pre className="report" style={{ fontSize: '0.78rem' }}>
        {JSON.stringify(data, null, 2)}
      </pre>
    </div>
  )
}
