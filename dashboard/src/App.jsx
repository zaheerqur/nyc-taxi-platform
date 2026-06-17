import { useState, useEffect } from 'react'
import { fetchTripVolume, fetchRevenue, fetchDemand, fetchMetrics } from './api'
import TripVolumeChart from './components/TripVolumeChart'
import RevenueBoroughChart from './components/RevenueBoroughChart'
import DemandHeatmap from './components/DemandHeatmap'
import FarePredictor from './components/FarePredictor'
import About from './components/About'

const REFRESH_MS = 60_000

export default function App() {
  const [page, setPage] = useState('dashboard')
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
        <span>Jan - Mar 2024</span>
        <nav className="nav">
          <button className={`nav-btn${page === 'dashboard' ? ' active' : ''}`} onClick={() => setPage('dashboard')}>Dashboard</button>
          <button className={`nav-btn${page === 'about' ? ' active' : ''}`} onClick={() => setPage('about')}>About</button>
          <a className="nav-btn nav-icon" href="https://github.com/zaheerqur/nyc-taxi-platform" target="_blank" rel="noreferrer" aria-label="GitHub">
            <svg height="18" width="18" viewBox="0 0 16 16" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
              <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/>
            </svg>
          </a>
        </nav>
      </header>

      {page === 'about' && <About />}

      {page === 'dashboard' && <>
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
          <FarePredictor onPredict={() => fetchMetrics().then(setMetrics)} />
        </div>
      </div>
      </>}
    </div>
  )
}
