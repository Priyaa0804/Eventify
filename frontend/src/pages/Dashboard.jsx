
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  LayoutDashboard,
  CalendarDays,
  ClipboardList,
  CheckCircle2,
  Bell,
  MapPin,
  LogOut,
  RefreshCw,
  Menu,
  X,
} from 'lucide-react'
import {
  getCurrentUser,
  getVenues,
  getMyEvents,
  getPendingApprovals,
  getCalendarEvents,
  getNotifications,
  logoutUser,
} from '../services/api'
import './Dashboard.css'

function getItems(data) {
  if (Array.isArray(data)) return data
  if (Array.isArray(data?.results)) return data.results
  if (Array.isArray(data?.events)) return data.events
  if (Array.isArray(data?.notifications)) return data.notifications
  if (Array.isArray(data?.venues)) return data.venues
  return []
}

function getEventTitle(event) {
  return event.title || event.event_name || event.name || 'Untitled event'
}

function getEventDate(event) {
  const value = event.event_date || event.date || event.start_date
  if (!value) return 'Date not specified'

  const date = new Date(value)
  return Number.isNaN(date.getTime())
    ? String(value)
    : date.toLocaleDateString()
}

function getStatus(event) {
  return String(event.status || event.current_status || 'Pending')
    .replaceAll('_', ' ')
}

export default function Dashboard() {
  const navigate = useNavigate()
  const [user, setUser] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('current_user') || '{}')
    } catch {
      return {}
    }
  })
  const [events, setEvents] = useState([])
  const [approvals, setApprovals] = useState([])
  const [venues, setVenues] = useState([])
  const [calendarEvents, setCalendarEvents] = useState([])
  const [notifications, setNotifications] = useState([])
  const [loading, setLoading] = useState(true)
  const [errors, setErrors] = useState([])
  const [activeSection, setActiveSection] = useState('Overview')
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  async function loadDashboard() {
    setLoading(true)
    setErrors([])

    const requests = [
      ['user', getCurrentUser],
      ['events', getMyEvents],
      ['approvals', getPendingApprovals],
      ['venues', getVenues],
      ['calendar', getCalendarEvents],
      ['notifications', getNotifications],
    ]

    const results = await Promise.allSettled(
      requests.map(([, request]) => request())
    )

    const failed = []

    results.forEach((result, index) => {
      const key = requests[index][0]

      if (result.status === 'rejected') {
        failed.push(key)
        return
      }

      const data = result.value

      if (key === 'user') {
        setUser(data)
        localStorage.setItem('current_user', JSON.stringify(data))
      } else if (key === 'events') {
        setEvents(getItems(data))
      } else if (key === 'approvals') {
        setApprovals(getItems(data))
      } else if (key === 'venues') {
        setVenues(getItems(data))
      } else if (key === 'calendar') {
        setCalendarEvents(getItems(data))
      } else if (key === 'notifications') {
        setNotifications(getItems(data))
      }
    })

    setErrors(failed)
    setLoading(false)
  }

  useEffect(() => {
    loadDashboard()
  }, [])

  function handleLogout() {
    logoutUser()
    localStorage.removeItem('current_user')
    navigate('/login', { replace: true })
  }

  const role = String(user.role || (user.is_superuser ? 'Administrator' : 'User'))
    .replaceAll('_', ' ')

  const navigation = [
    { label: 'Overview', icon: LayoutDashboard },
    { label: 'My Events', icon: ClipboardList },
    { label: 'Approvals', icon: CheckCircle2 },
    { label: 'Calendar', icon: CalendarDays },
    { label: 'Venues', icon: MapPin },
    { label: 'Notifications', icon: Bell },
  ]

  function renderSection() {
    if (activeSection === 'Overview') {
      return (
        <>
          <div className="dashboard-welcome">
            <div>
              <p className="dashboard-eyebrow">EVENT MANAGEMENT PORTAL</p>
              <h1>Welcome back{user.username ? `, ${user.username}` : ''}</h1>
              <p>Here is an overview of your event management workspace.</p>
            </div>
            <button className="dashboard-refresh" onClick={loadDashboard}>
              <RefreshCw size={16} />
              Refresh
            </button>
          </div>

          <div className="dashboard-stats">
            <article className="dashboard-stat">
              <span className="stat-icon"><ClipboardList size={20} /></span>
              <p>My event requests</p>
              <strong>{events.length}</strong>
              <span>Requests returned by the server</span>
            </article>
            <article className="dashboard-stat">
              <span className="stat-icon"><CheckCircle2 size={20} /></span>
              <p>Pending approvals</p>
              <strong>{approvals.length}</strong>
              <span>Items awaiting approval</span>
            </article>
            <article className="dashboard-stat">
              <span className="stat-icon"><CalendarDays size={20} /></span>
              <p>Calendar events</p>
              <strong>{calendarEvents.length}</strong>
              <span>Events returned by the calendar API</span>
            </article>
            <article className="dashboard-stat">
              <span className="stat-icon"><Bell size={20} /></span>
              <p>Notifications</p>
              <strong>{notifications.length}</strong>
              <span>Notifications returned by the server</span>
            </article>
          </div>

          {errors.length > 0 && (
            <div className="dashboard-warning" role="status">
              Some data could not be loaded: {errors.join(', ')}.
              Your account may not have permission to access every endpoint.
              <button onClick={loadDashboard}>Try again</button>
            </div>
          )}

          <section className="dashboard-panel">
            <div className="dashboard-panel-heading">
              <div>
                <h2>My event requests</h2>
                <p>Your latest requests from the backend</p>
              </div>
              <button className="dashboard-text-button" onClick={() => setActiveSection('My Events')}>
                View all
              </button>
            </div>
            <EventList events={events.slice(0, 5)} loading={loading} />
          </section>

          <section className="dashboard-panel">
            <div className="dashboard-panel-heading">
              <div>
                <h2>Pending approvals</h2>
                <p>Requests returned by the approvals API</p>
              </div>
              <button className="dashboard-text-button" onClick={() => setActiveSection('Approvals')}>
                View all
              </button>
            </div>
            <EventList events={approvals.slice(0, 5)} loading={loading} />
          </section>
        </>
      )
    }

    if (activeSection === 'My Events') {
      return <DataSection title="My Events" description="Your event requests." events={events} loading={loading} />
    }

    if (activeSection === 'Approvals') {
      return <DataSection title="Approvals" description="Pending event requests available to your account." events={approvals} loading={loading} />
    }

    if (activeSection === 'Calendar') {
      return <DataSection title="Calendar Events" description="Events returned by the calendar API." events={calendarEvents} loading={loading} />
    }

    if (activeSection === 'Venues') {
      return (
        <section className="dashboard-panel">
          <div className="dashboard-panel-heading">
            <div>
              <h2>Venues</h2>
              <p>Venues returned by the backend</p>
            </div>
          </div>
          {loading ? <p className="dashboard-empty">Loading venues...</p> :
            venues.length === 0 ? <p className="dashboard-empty">No venues were returned by the API.</p> :
              <div className="dashboard-data-list">
                {venues.map((venue, index) => (
                  <article className="dashboard-data-row" key={venue.id || index}>
                    <span className="event-list-icon"><MapPin size={18} /></span>
                    <div className="event-list-main">
                      <strong>{venue.name || venue.venue_name || `Venue ${index + 1}`}</strong>
                      <p>{venue.location || venue.building || venue.description || 'Venue details not provided'}</p>
                    </div>
                  </article>
                ))}
              </div>}
        </section>
      )
    }

    return (
      <section className="dashboard-panel">
        <div className="dashboard-panel-heading">
          <div>
            <h2>Notifications</h2>
            <p>Notifications returned by the backend</p>
          </div>
        </div>
        {loading ? <p className="dashboard-empty">Loading notifications...</p> :
          notifications.length === 0 ? <p className="dashboard-empty">No notifications were returned by the API.</p> :
            <div className="dashboard-data-list">
              {notifications.map((item, index) => (
                <article className="dashboard-data-row" key={item.id || index}>
                  <span className="event-list-icon"><Bell size={18} /></span>
                  <div className="event-list-main">
                    <strong>{item.title || item.message || item.description || 'Notification'}</strong>
                    <p>{item.created_at ? new Date(item.created_at).toLocaleString() : 'Date not provided'}</p>
                  </div>
                </article>
              ))}
            </div>}
      </section>
    )
  }

  return (
    <div className="dashboard-layout">
      {mobileMenuOpen && (
        <button className="dashboard-mobile-backdrop" aria-label="Close navigation" onClick={() => setMobileMenuOpen(false)} />
      )}

      <aside className={`dashboard-sidebar ${mobileMenuOpen ? 'dashboard-sidebar-open' : ''}`}>
        <div className="dashboard-brand-row">
          <div className="dashboard-brand-mark">E</div>
          <span className="dashboard-brand-name">Eventify</span>
          <button className="dashboard-close-menu" aria-label="Close menu" onClick={() => setMobileMenuOpen(false)}>
            <X size={20} />
          </button>
        </div>

        <p className="dashboard-nav-label">WORKSPACE</p>
        <nav className="dashboard-nav">
          {navigation.map(({ label, icon: Icon }) => (
            <button
              key={label}
              className={`dashboard-nav-item ${activeSection === label ? 'active' : ''}`}
              onClick={() => {
                setActiveSection(label)
                setMobileMenuOpen(false)
              }}
            >
              <Icon size={18} />
              <span>{label}</span>
              {label === 'Notifications' && notifications.length > 0 && (
                <span className="dashboard-nav-count">{notifications.length}</span>
              )}
            </button>
          ))}
        </nav>

        <div className="dashboard-sidebar-bottom">
          <div className="dashboard-user">
            <div className="dashboard-avatar">
              {(user.username || 'U').slice(0, 1).toUpperCase()}
            </div>
            <div className="dashboard-user-info">
              <strong>{user.username || 'Logged-in user'}</strong>
              <span>{role}</span>
            </div>
          </div>
          <button className="dashboard-logout" onClick={handleLogout}>
            <LogOut size={17} />
            Sign out
          </button>
        </div>
      </aside>

      <main className="dashboard-main">
        <header className="dashboard-topbar">
          <button className="dashboard-open-menu" aria-label="Open menu" onClick={() => setMobileMenuOpen(true)}>
            <Menu size={21} />
          </button>
          <span className="dashboard-breadcrumb">Workspace / <strong>{activeSection}</strong></span>
          <div className="dashboard-topbar-actions">
            <span className="dashboard-role-label">{role}</span>
            <button className="dashboard-icon-button" aria-label="Notifications" onClick={() => setActiveSection('Notifications')}>
              <Bell size={19} />
              {notifications.length > 0 && <i />}
            </button>
          </div>
        </header>

        <div className="dashboard-content">
          {renderSection()}
        </div>
      </main>
    </div>
  )
}

function EventList({ events, loading }) {
  if (loading) return <p className="dashboard-empty">Loading data from the backend...</p>
  if (events.length === 0) return <p className="dashboard-empty">No records were returned by the API.</p>

  return (
    <div className="dashboard-data-list">
      {events.map((event, index) => (
        <article className="dashboard-data-row" key={event.id || index}>
          <span className="event-list-icon"><CalendarDays size={18} /></span>
          <div className="event-list-main">
            <strong>{getEventTitle(event)}</strong>
            <p>{getEventDate(event)}</p>
          </div>
          <span className="event-status">{getStatus(event)}</span>
        </article>
      ))}
    </div>
  )
}

function DataSection({ title, description, events, loading }) {
  return (
    <section className="dashboard-panel dashboard-full-panel">
      <div className="dashboard-panel-heading">
        <div>
          <h2>{title}</h2>
          <p>{description}</p>
        </div>
      </div>
      <EventList events={events} loading={loading} />
    </section>
  )
}
