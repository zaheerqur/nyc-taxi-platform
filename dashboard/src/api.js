const BASE = import.meta.env.VITE_API_URL || ''

export async function fetchTripVolume() {
  const r = await fetch(`${BASE}/stats/trip-volume`)
  return r.json()
}

export async function fetchRevenue() {
  const r = await fetch(`${BASE}/stats/revenue`)
  return r.json()
}

export async function fetchDemand() {
  const r = await fetch(`${BASE}/stats/demand`)
  return r.json()
}

export async function fetchMetrics() {
  const r = await fetch(`${BASE}/metrics`)
  return r.json()
}

export async function postPredict(features) {
  const r = await fetch(`${BASE}/predict`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(features),
  })
  return r.json()
}
