import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell } from 'recharts'

const COLORS = ['#63b3ed', '#76e4f7', '#9ae6b4', '#fbd38d', '#fc8181']

export default function RevenueBoroughChart({ data }) {
  if (!data.length) return <div className="loading">No data</div>

  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#2d3748" />
        <XAxis dataKey="borough" tick={{ fill: '#718096', fontSize: 11 }} />
        <YAxis tick={{ fill: '#718096', fontSize: 11 }} width={56} tickFormatter={v => `$${(v / 1000).toFixed(0)}k`} />
        <Tooltip
          contentStyle={{ background: '#1e2130', border: '1px solid #2d3748', borderRadius: 6 }}
          labelStyle={{ color: '#a0aec0' }}
          formatter={v => [`$${v.toLocaleString()}`, 'Revenue']}
        />
        <Bar dataKey="revenue" radius={[4, 4, 0, 0]}>
          {data.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
