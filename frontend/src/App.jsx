import { useState } from 'react'

// In dev, Vite proxies /api -> http://127.0.0.1:8000 (see vite.config.js).
const API = '/api'

const SAMPLE_JOB = `Job Title: Backend Engineer
We are hiring a Backend Engineer with 3+ years of experience.
Requirements:
- Strong experience with Python, FastAPI, and PostgreSQL
- Experience with Docker and REST APIs
- Familiarity with Redis and microservices`

const SAMPLE_CANDIDATES = [
  {
    name: 'Ava Chen',
    text: `Ava Chen
Backend Engineer with 5+ years of experience.
Skills: Python, FastAPI, PostgreSQL, Docker, REST API, Redis, microservices, Git
Backend Engineer at Globex (2019 - Present)
Education: Bachelor's in Computer Science`,
  },
  {
    name: 'Ben Ortiz',
    text: `Ben Ortiz
Frontend Engineer with 4+ years of experience.
Skills: React, JavaScript, TypeScript, CSS, Redux, HTML
Education: Bachelor's in Software Engineering`,
  },
]

function scoreColor(score) {
  if (score >= 0.6) return 'var(--good)'
  if (score >= 0.4) return 'var(--mid)'
  return 'var(--bad)'
}

export default function App() {
  const [job, setJob] = useState(SAMPLE_JOB)
  const [candidates, setCandidates] = useState(SAMPLE_CANDIDATES)
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const updateCandidate = (i, field, value) => {
    setCandidates((cs) => cs.map((c, idx) => (idx === i ? { ...c, [field]: value } : c)))
  }
  const addCandidate = () => setCandidates((cs) => [...cs, { name: '', text: '' }])
  const removeCandidate = (i) => setCandidates((cs) => cs.filter((_, idx) => idx !== i))

  const rankCandidates = async () => {
    setLoading(true)
    setError(null)
    setResults(null)
    try {
      const res = await fetch(`${API}/rank`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_description: job,
          candidates: candidates.filter((c) => c.text.trim()),
        }),
      })
      if (!res.ok) throw new Error(`Server responded ${res.status}`)
      const data = await res.json()
      setResults(data)
    } catch (e) {
      setError(`${e.message}. Is the backend running on port 8000?`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <header>
        <h1>AI Resume Screener</h1>
        <p className="sub">Rank candidates against a job description with an explainable NLP score.</p>
      </header>

      <section className="panel">
        <h2>Job description</h2>
        <textarea value={job} onChange={(e) => setJob(e.target.value)} rows={8} />
      </section>

      <section className="panel">
        <div className="row-between">
          <h2>Candidates ({candidates.length})</h2>
          <button className="ghost" onClick={addCandidate}>+ Add candidate</button>
        </div>
        {candidates.map((c, i) => (
          <div className="candidate-input" key={i}>
            <div className="row-between">
              <input
                className="name"
                placeholder="Candidate name (optional)"
                value={c.name}
                onChange={(e) => updateCandidate(i, 'name', e.target.value)}
              />
              <button className="ghost danger" onClick={() => removeCandidate(i)}>Remove</button>
            </div>
            <textarea
              placeholder="Paste resume text…"
              value={c.text}
              rows={5}
              onChange={(e) => updateCandidate(i, 'text', e.target.value)}
            />
          </div>
        ))}
      </section>

      <button className="primary" onClick={rankCandidates} disabled={loading}>
        {loading ? 'Scoring…' : 'Score & Rank'}
      </button>

      {error && <p className="error">{error}</p>}

      {results && (
        <section className="panel results">
          <h2>Ranking</h2>
          <p className="muted">
            Required skills: {results.job.required_skills.join(', ') || '—'} · Min years:{' '}
            {results.job.min_years}
          </p>
          {results.results.map((r, i) => (
            <div className="result-card" key={i}>
              <div className="result-head">
                <span className="rank">#{i + 1}</span>
                <span className="cand-name">{r.candidate.name || 'Unknown'}</span>
                <span className="score" style={{ color: scoreColor(r.score) }}>
                  {(r.score * 100).toFixed(0)}%
                </span>
                <span className={`badge ${r.is_match ? 'match' : 'nomatch'}`}>
                  {r.is_match ? 'MATCH' : 'no match'}
                </span>
              </div>
              <div className="bar">
                <div className="bar-fill" style={{ width: `${r.score * 100}%`, background: scoreColor(r.score) }} />
              </div>
              <div className="skills">
                {r.matched_skills.map((s) => (
                  <span className="chip matched" key={s}>{s}</span>
                ))}
                {r.missing_skills.map((s) => (
                  <span className="chip missing" key={s}>{s}</span>
                ))}
              </div>
              <div className="meta">
                <span>Skill coverage: {(r.breakdown.skill_coverage * 100).toFixed(0)}%</span>
                <span>Similarity: {(r.breakdown.similarity * 100).toFixed(0)}%</span>
                <span>Experience: {r.candidate.years_experience} yrs</span>
                {r.candidate.highest_degree && <span>{r.candidate.highest_degree}</span>}
              </div>
            </div>
          ))}
        </section>
      )}

      <footer>NLP extraction + TF-IDF & skill-overlap ranking · FastAPI + React</footer>
    </div>
  )
}
