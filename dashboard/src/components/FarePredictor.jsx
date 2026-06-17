import { useState } from 'react'
import { postPredict } from '../api'

const DEFAULTS = {
  trip_distance: 3.5,
  hour_of_day: 14,
  day_of_week: 2,
  pu_location_id: 161,
  do_location_id: 237,
  passenger_count: 1,
}

const LABELS = {
  trip_distance: 'Distance (miles)',
  hour_of_day: 'Hour (0-23)',
  day_of_week: 'Day of week (0=Sun)',
  pu_location_id: 'Pickup zone ID',
  do_location_id: 'Dropoff zone ID',
  passenger_count: 'Passengers',
}

export default function FarePredictor({ onPredict }) {
  const [form, setForm] = useState(DEFAULTS)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleChange = e => {
    setForm(f => ({ ...f, [e.target.name]: Number(e.target.value) }))
  }

  const handleSubmit = async e => {
    e.preventDefault()
    setLoading(true)
    try {
      const data = await postPredict(form)
      setResult(data)
      if (onPredict) onPredict()
    } catch {
      setResult(null)
    } finally {
      setLoading(false)
    }
  }

  return (
    <form className="predictor-form" onSubmit={handleSubmit}>
      {Object.entries(DEFAULTS).map(([key]) => (
        <div key={key} className="field">
          <label>{LABELS[key]}</label>
          <input
            name={key}
            type="number"
            step="any"
            value={form[key]}
            onChange={handleChange}
          />
        </div>
      ))}
      <button className="predict-btn" type="submit" disabled={loading}>
        {loading ? 'Predicting...' : 'Predict Fare'}
      </button>
      {result && (
        <div className="fare-result">
          <div className="fare-amount">${result.predicted_fare}</div>
          <div className="fare-label">model v{result.model_version}</div>
        </div>
      )}
    </form>
  )
}
