const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
const HOURS = Array.from({ length: 24 }, (_, i) => i)

function getColor(ratio) {
  const r = Math.round(20 + ratio * 220)
  const g = Math.round(30 + ratio * 80)
  const b = Math.round(180 - ratio * 150)
  return `rgb(${r},${g},${b})`
}

export default function DemandHeatmap({ data }) {
  if (!data.length) return <div className="loading">No data</div>

  const max = Math.max(...data.map(d => d.trips), 1)
  const lookup = {}
  data.forEach(({ hour, day, trips }) => {
    if (!lookup[day]) lookup[day] = {}
    lookup[day][hour] = trips
  })

  return (
    <div className="heatmap-wrap">
      <div className="heatmap-grid">
        <div />
        {HOURS.map(h => (
          <div key={h} className="heatmap-hour-label">{h % 6 === 0 ? h : ''}</div>
        ))}
        {DAYS.map((day, d) => (
          <>
            <div key={`label-${d}`} className="heatmap-day-label">{day}</div>
            {HOURS.map(h => {
              const trips = lookup[d]?.[h] ?? 0
              return (
                <div
                  key={h}
                  className="heatmap-cell"
                  style={{ background: getColor(trips / max) }}
                  title={`${day} ${h}:00 - ${trips.toLocaleString()} trips`}
                />
              )
            })}
          </>
        ))}
      </div>
    </div>
  )
}
