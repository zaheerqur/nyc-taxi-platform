import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'

export default function TripVolumeChart({ data }) {
  if (!data.length) return <div className="loading">No data</div>

  const formatted = data.map(d => ({
    ...d,
    date: d.date.slice(5),  // "01-03" instead of "2024-01-03"
  }))

  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={formatted} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#2d3748" />
        <XAxis dataKey="date" tick={{ fill: '#718096', fontSize: 11 }} />
        <YAxis tick={{ fill: '#718096', fontSize: 11 }} width={48} tickFormatter={v => v.toLocaleString()} />
        <Tooltip
          contentStyle={{ background: '#1e2130', border: '1px solid #2d3748', borderRadius: 6 }}
          labelStyle={{ color: '#a0aec0' }}
          formatter={v => [v.toLocaleString(), 'Trips']}
        />
        <Line type="monotone" dataKey="trips" stroke="#63b3ed" strokeWidth={2} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  )
}
