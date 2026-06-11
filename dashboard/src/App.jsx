import { useState, useEffect } from 'react'
import { fetchTripVolume, fetchRevenue, fetchDemand, fetchMetrics } from './api'
import TripVolumeChart from './components/TripVolumeChart'
import RevenueBoroughChart from './components/RevenueBoroughChart'
import DemandHeatmap from './components/DemandHeatmap'
import FarePredictor from './components/FarePredictor'

const REFRESH_MS = 60_000

export default function App() {
  const [tripVolume, setTripVolume] = useState([])
  const [revenue, setRevenue] = useState([])
  const [demand, setDemand] = useState([])
  const [metrics, setMetrics] = useState(null)

  const load = async () => {
    const [tv, rev, dem, met] = await Promise.all([
      fetchTripVolume(),
      fetchRevenue(),
      fetchDemand(),
      fetchMetrics(),
    ])
    setTripVolume(tv)
    setRevenue(rev)
    setDemand(dem)
    setMetrics(met)
  }

  useEffect(() => {
    load()
    const id = setInterval(load, REFRESH_MS)
    return () => clearInterval(id)
  }, [])

  const totalTrips = tripVolume.reduce((s, d) => s + d.trips, 0)
  const totalRevenue = revenue.reduce((s, d) => s + d.revenue, 0)

  return (
    <div className="app">
      <header>
        <h1>NYC Taxi Analytics</h1>
        <span>Jan - Mar 2024 &nbsp;·&nbsp; refreshes every 60s</span>
      </header>

      <div className="stats-bar">
        <div className="stat-card">
          <div className="label">Total Trips</div>
          <div className="value">{totalTrips.toLocaleString()}</div>
        </div>
        <div className="stat-card">
          <div className="label">Total Revenue</div>
          <div className="value">${totalRevenue.toLocaleString(undefined, { maximumFractionDigits: 0 })}</div>
        </div>
        <div className="stat-card">
          <div className="label">Predictions Served</div>
          <div className="value">{metrics?.total_predictions ?? 0}</div>
        </div>
        <div className="stat-card">
          <div className="label">Avg Predicted Fare</div>
          <div className="value">{metrics?.avg_predicted_fare ? `$${metrics.avg_predicted_fare}` : '-'}</div>
        </div>
      </div>

      <div className="grid">
        <div className="card">
          <h2>Daily Trip Volume</h2>
          <TripVolumeChart data={tripVolume} />
        </div>
        <div className="card">
          <h2>Revenue by Borough</h2>
          <RevenueBoroughChart data={revenue} />
        </div>
        <div className="card">
          <h2>Peak Demand - Hour x Day</h2>
          <DemandHeatmap data={demand} />
        </div>
        <div className="card">
          <h2>Fare Predictor</h2>
          <FarePredictor />
        </div>
      </div>
    </div>
  )
}
