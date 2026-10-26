
import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import api from '../services/api'
import './CreateEvent.css'

export default function CreateEvent() {
  const navigate = useNavigate()

  const [clubs, setClubs] = useState([])
  const [venues, setVenues] = useState([])
  const [loadingOptions, setLoadingOptions] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const [formData, setFormData] = useState({
    event_name: '',
    club: '',
    venue: '',
    event_date: '',
    start_time: '',
    end_time: '',
    expected_participants: '',
    description: '',
    additional_requirements: '',
  })

  useEffect(() => {
    async function loadOptions() {
      try {
        const [clubResponse, venueResponse] = await Promise.all([
          api.get('clubs/'),
          api.get('venues/'),
        ])

        const clubData = clubResponse.data
        const venueData = venueResponse.data

        setClubs(
          Array.isArray(clubData) ? clubData : clubData.results || []
        )

        setVenues(
          Array.isArray(venueData) ? venueData : venueData.results || []
        )
      } catch (err) {
        setError(
          'Could not load clubs or venues. Please check your connection and login.'
        )
      } finally {
        setLoadingOptions(false)
      }
    }

    loadOptions()
  }, [])

  function handleChange(event) {
    const { name, value } = event.target

    setFormData((previous) => ({
      ...previous,
      [name]: value,
    }))
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setSuccess('')

    if (formData.start_time >= formData.end_time) {
      setError('End time must be later than start time.')
      return
    }

    if (Number(formData.expected_participants) < 1) {
      setError('Expected participants must be at least 1.')
      return
    }

    setSubmitting(true)

    try {
      const payload = {
        event_name: formData.event_name.trim(),
        club: Number(formData.club),
        venue: Number(formData.venue),
        event_date: formData.event_date,
        start_time: formData.start_time,
        end_time: formData.end_time,
        expected_participants: Number(formData.expected_participants),
        description: formData.description.trim(),
        additional_requirements: formData.additional_requirements.trim(),
      }

      await api.post('events/', payload)

      setSuccess('Event request submitted successfully!')
      setFormData({
        event_name: '',
        club: '',
        venue: '',
        event_date: '',
        start_time: '',
        end_time: '',
        expected_participants: '',
        description: '',
        additional_requirements: '',
      })

      setTimeout(() => navigate('/student'), 1200)
    } catch (err) {
      const data = err.response?.data

      if (data && typeof data === 'object') {
        const messages = Object.entries(data)
          .map(([field, value]) => {
            const text = Array.isArray(value)
              ? value.join(', ')
              : typeof value === 'string'
                ? value
                : JSON.stringify(value)

            return `${field}: ${text}`
          })
          .join(' ')

        setError(messages || 'Could not submit the event request.')
      } else {
        setError(
          'Could not submit the event request. Please check your login and backend server.'
        )
      }
    } finally {
      setSubmitting(false)
    }
  }

  if (loadingOptions) {
    return (
      <main className="create-event-page">
        <section className="create-event-card">
          <p>Loading clubs and venues...</p>
        </section>
      </main>
    )
  }

  return (
    <main className="create-event-page">
      <section className="create-event-card">
        <Link to="/student" className="create-event-back">
          ← Back to Dashboard
        </Link>

        <div className="create-event-heading">
          <p className="create-event-eyebrow">EVENTIFY · STUDENT PORTAL</p>
          <h1>Create Event Request</h1>
          <p>
            Submit your college event details for approval.
          </p>
        </div>

        {error && (
          <div className="create-event-error" role="alert">
            {error}
          </div>
        )}

        {success && (
          <div className="create-event-success" role="status">
            {success}
          </div>
        )}

        <form onSubmit={handleSubmit} className="create-event-form">
          <label htmlFor="event_name">Event Name *</label>
          <input
            id="event_name"
            name="event_name"
            value={formData.event_name}
            onChange={handleChange}
            placeholder="e.g. Annual Tech Fest"
            maxLength={200}
            required
          />

          <label htmlFor="club">Club *</label>
          <select
            id="club"
            name="club"
            value={formData.club}
            onChange={handleChange}
            required
          >
            <option value="">Select a club</option>
            {clubs.map((club) => (
              <option key={club.id} value={club.id}>
                {club.name} — {club.department}
              </option>
            ))}
          </select>

          <label htmlFor="venue">Venue *</label>
          <select
            id="venue"
            name="venue"
            value={formData.venue}
            onChange={handleChange}
            required
          >
            <option value="">Select a venue</option>
            {venues.map((venue) => (
              <option key={venue.id} value={venue.id}>
                {venue.name} (Capacity: {venue.capacity})
              </option>
            ))}
          </select>

          {venues.length === 0 && (
            <p className="create-event-hint">
              No active venues are available yet. A faculty advisor or HOD
              needs to add a venue before you can submit an event request.
            </p>
          )}

          <label htmlFor="event_date">Event Date *</label>
          <input
            id="event_date"
            name="event_date"
            type="date"
            value={formData.event_date}
            onChange={handleChange}
            min={new Date().toLocaleDateString('en-CA')}
            required
          />

          <div className="create-event-time-row">
            <div>
              <label htmlFor="start_time">Start Time *</label>
              <input
                id="start_time"
                name="start_time"
                type="time"
                value={formData.start_time}
                onChange={handleChange}
                required
              />
            </div>

            <div>
              <label htmlFor="end_time">End Time *</label>
              <input
                id="end_time"
                name="end_time"
                type="time"
                value={formData.end_time}
                onChange={handleChange}
                required
              />
            </div>
          </div>

          <label htmlFor="expected_participants">
            Expected Participants *
          </label>
          <input
            id="expected_participants"
            name="expected_participants"
            type="number"
            min="1"
            value={formData.expected_participants}
            onChange={handleChange}
            placeholder="e.g. 150"
            required
          />

          <label htmlFor="description">Event Description</label>
          <textarea
            id="description"
            name="description"
            value={formData.description}
            onChange={handleChange}
            placeholder="Describe your event..."
            rows={4}
          />

          <label htmlFor="additional_requirements">
            Additional Requirements
          </label>
          <textarea
            id="additional_requirements"
            name="additional_requirements"
            value={formData.additional_requirements}
            onChange={handleChange}
            placeholder="Projector, microphones, seating, etc."
            rows={3}
          />

          <button
            type="submit"
            disabled={submitting || venues.length === 0}
          >
            {submitting ? 'Submitting Request...' : 'Submit Event Request'}
          </button>
        </form>
      </section>
    </main>
  )
}
