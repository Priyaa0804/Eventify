
import { useState } from 'react'
import { useLocation, useNavigate, Link } from 'react-router-dom'
import { loginUser, getCurrentUser } from '../services/api'
import './Login.css'

export default function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const navigate = useNavigate()
  const location = useLocation()
  const successMessage = location.state?.message

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setLoading(true)

    try {
      await loginUser(username, password)
      const user = await getCurrentUser()

      localStorage.setItem('current_user', JSON.stringify(user))

      const role = String(user.role || '').toUpperCase()

      if (role === 'STUDENT') {
        navigate('/student')
      } else if (role === 'FACULTY_ADVISOR' || role === 'FACULTY') {
        navigate('/faculty')
      } else if (role === 'HOD') {
        navigate('/hod')
      } else {
        navigate('/dashboard')
      }
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        err.response?.data?.non_field_errors?.[0] ||
        'Login failed. Check your username, password, and backend server.'
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="login-page">
      <section className="login-card">
        <div className="login-brand">EventFlow</div>
        <p className="login-eyebrow">EVENT MANAGEMENT PORTAL</p>

        <h1>Welcome back</h1>

        <p className="login-subtitle">
          Sign in to manage your college events.
        </p>

        {successMessage && (
          <p className="login-success" role="status">
            {successMessage}
          </p>
        )}

        <form onSubmit={handleSubmit}>
          <label htmlFor="username">Username</label>
          <input
            id="username"
            autoComplete="username"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            placeholder="Enter your username"
            required
          />

          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="Enter your password"
            required
          />

          {error && (
            <p className="login-error" role="alert">
              {error}
            </p>
          )}

          <button type="submit" disabled={loading}>
            {loading ? 'Signing in...' : 'Sign in'}
          </button>
        </form>

        <p className="login-register">
          Don't have an account? <Link to="/register">Create Account</Link>
        </p>

        <p className="login-footer">
          Event requests · Approvals · Venue calendar
        </p>
      </section>
    </main>
  )
}
