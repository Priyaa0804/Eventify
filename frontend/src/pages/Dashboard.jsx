
import { useCallback, useEffect, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  CalendarDays,
  LayoutDashboard,
  Bell,
  MapPin,
  ShieldCheck,
  LogOut,
  Plus,
  RefreshCw,
  Clock3,
  Check,
  X,
} from 'lucide-react';

import {
  me,
  myEvents,
  pending,
  venues,
  calendar,
  notifications,
  approve,
  reject,
  logout,
} from '../services/api.js';

const fmt = (value) => {
  if (!value) return 'Not scheduled';

  const date = new Date(`${String(value).slice(0, 10)}T00:00:00`);

  return Number.isNaN(date.getTime())
    ? value
    : date.toLocaleDateString(undefined, {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
      });
};

const fmtTime = (value) => {
  if (!value) return 'Time unavailable';

  const timePart = String(value).match(/T(\d{2}):(\d{2})/);

  if (timePart) {
    const hours = Number(timePart[1]);
    const minutes = Number(timePart[2]);
    const date = new Date();
    date.setHours(hours, minutes, 0, 0);

    return date.toLocaleTimeString('en-IN', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: true,
    });
  }

  const plainTime = String(value).match(/^(\d{2}):(\d{2})/);

  if (plainTime) {
    const hours = Number(plainTime[1]);
    const minutes = Number(plainTime[2]);
    const date = new Date();
    date.setHours(hours, minutes, 0, 0);

    return date.toLocaleTimeString('en-IN', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: true,
    });
  }

  return 'Time unavailable';
};

const pretty = (value) =>
  String(value || 'pending')
    .replaceAll('_', ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase());

export default function Dashboard() {
  const nav = useNavigate();
  const loc = useLocation();

  const [user, setUser] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('current_user') || '{}');
    } catch {
      return {};
    }
  });

  const [events, setEvents] = useState([]);
  const [approvals, setApprovals] = useState([]);
  const [venueList, setVenueList] = useState([]);
  const [calendarEvents, setCalendarEvents] = useState([]);
  const [notes, setNotes] = useState([]);
  const [section, setSection] = useState('Overview');
  const [error, setError] = useState('');
  const [notice, setNotice] = useState(loc.state?.notice || '');
  const [busy, setBusy] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');

    const results = await Promise.allSettled([
      me(),
      myEvents(),
      pending(),
      venues(),
      calendar(),
      notifications(),
    ]);

    if (results[0].status === 'fulfilled') {
      setUser(results[0].value);
      localStorage.setItem(
        'current_user',
        JSON.stringify(results[0].value)
      );
    } else if (results[0].reason?.response?.status === 401) {
      logout();
      nav('/login');
      return;
    }

    if (results[1].status === 'fulfilled') {
      setEvents(results[1].value);
    }

    if (results[2].status === 'fulfilled') {
      setApprovals(results[2].value);
    }

    if (results[3].status === 'fulfilled') {
      setVenueList(results[3].value);
    }

    if (results[4].status === 'fulfilled') {
      setCalendarEvents(results[4].value);
    }

    if (results[5].status === 'fulfilled') {
      setNotes(results[5].value);
    }

    if (results.every((result) => result.status === 'rejected')) {
      setError(
        'Could not reach Django. Start the backend at 127.0.0.1:8000 and sign in again.'
      );
    }

    setLoading(false);
  }, [nav]);

  useEffect(() => {
    load();
  }, [load]);

  const role = String(user.role || 'STUDENT').toUpperCase();
  const canApprove = ['FACULTY_ADVISOR', 'HOD'].includes(role);

  const navItems = [
    ['Overview', LayoutDashboard],
    ['My Events', CalendarDays],
    ...(canApprove ? [['Approvals', ShieldCheck]] : []),
    ['Calendar', Clock3],
    ['Venues', MapPin],
    ['Notifications', Bell],
  ];

  async function decide(id, kind) {
    setBusy(id);
    setError('');

    try {
      if (kind === 'approve') {
        await approve(id);
      } else {
        await reject(id);
      }

      setNotice(
        `Request ${kind === 'approve' ? 'approved' : 'rejected'}.`
      );

      await load();
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          'Action failed. Check the account role and approval assignment.'
      );
    } finally {
      setBusy(null);
    }
  }

  function signout() {
    logout();
    nav('/login');
  }

  return (
    <div className="dashboard">
      <aside className="sidebar">
        <Link className="brand" to="/dashboard">
          <CalendarDays /> eventify<span>.</span>
        </Link>

        <small>WORKSPACE</small>

        {navItems.map(([name, Icon]) => (
          <button
            className={section === name ? 'nav active' : 'nav'}
            key={name}
            onClick={() => setSection(name)}
          >
            <Icon size={18} />
            {name}
            {name === 'Approvals' && approvals.length > 0 && (
              <b>{approvals.length}</b>
            )}
          </button>
        ))}

        <div className="side-bottom">
          <div className="user">
            <span>{(user.username || 'U')[0].toUpperCase()}</span>
            <div>
              <strong>{user.username || 'Campus user'}</strong>
              <small>{pretty(role)}</small>
            </div>
          </div>

          <button className="nav" onClick={signout}>
            <LogOut size={18} /> Sign out
          </button>
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <span>
            Workspace / <b>{section}</b>
          </span>

          <div>
            <span className="live">● Local API</span>
            <button className="round" onClick={load} title="Refresh">
              <RefreshCw size={17} />
            </button>
          </div>
        </header>

        <div className="content">
          {notice && (
            <div className="success">
              {notice}
              <button onClick={() => setNotice('')}>×</button>
            </div>
          )}

          {error && <div className="error">{error}</div>}

          <div className="heading">
            <div>
              <small className="kicker">EVENTIFY CAMPUS PORTAL</small>
              <h1>
                {section === 'Overview'
                  ? `Welcome back${user.username ? `, ${user.username}` : ''}`
                  : section}
              </h1>
              <p className="muted">
                Your plans, people and progress — all in one place.
              </p>
            </div>

            {!['Approvals', 'Notifications'].includes(section) && (
              <Link className="primary" to="/create-event">
                <Plus size={17} /> Create event
              </Link>
            )}
          </div>

          {section === 'Overview' && (
            <>
              <div className="stats">
                <Stat label="My event requests" n={events.length} icon={CalendarDays} />
                <Stat label="Awaiting review" n={approvals.length} icon={ShieldCheck} />
                <Stat label="Available venues" n={venueList.length} icon={MapPin} />
                <Stat label="Notifications" n={notes.length} icon={Bell} />
              </div>

              <div className="panels">
                <Panel title="Recent event requests" action={() => setSection('My Events')}>
                  {loading ? (
                    <Loading />
                  ) : events.length ? (
                    events.slice(0, 5).map((event) => (
                      <Event key={event.id} e={event} />
                    ))
                  ) : (
                    <Empty text="No event requests yet. Create your first campus event." />
                  )}
                </Panel>

                <Panel title="Recent notifications" action={() => setSection('Notifications')}>
                  {loading ? (
                    <Loading />
                  ) : notes.length ? (
                    notes.slice(0, 5).map((note) => (
                      <div className="note" key={note.id}>
                        <b>{note.title || note.event_name || 'Event update'}</b>
                        <p>{note.message || 'There is an update on your request.'}</p>
                      </div>
                    ))
                  ) : (
                    <Empty text="You are all caught up." />
                  )}
                </Panel>
              </div>
            </>
          )}

          {section === 'My Events' && (
            <Panel title="All my event requests">
              {loading ? (
                <Loading />
              ) : events.length ? (
                events.map((event) => <Event key={event.id} e={event} />)
              ) : (
                <Empty text="No requests yet. Create an event to get started." />
              )}
            </Panel>
          )}

          {section === 'Approvals' && (
            <Panel title="Requests needing review">
              {loading ? (
                <Loading />
              ) : approvals.length ? (
                approvals.map((event) => (
                  <article className="approval" key={event.id}>
                    <div>
                      <h3>{event.event_name}</h3>
                      <p>{event.description || 'No description provided'}</p>
                      <small>
                        {fmt(event.event_date)} · {pretty(event.status)}
                      </small>
                      <small style={{ display: 'block', marginTop: '5px' }}>
                        <Clock3 size={13} style={{ verticalAlign: 'middle', marginRight: '5px' }} />
                        {event.start_time?.slice(0, 5) || 'Time TBD'} – {event.end_time?.slice(0, 5) || 'Time TBD'}
                      </small>
                    </div>

                    <div className="actions">
                      <button
                        className="primary"
                        disabled={busy === event.id}
                        onClick={() => decide(event.id, 'approve')}
                      >
                        <Check size={15} /> Approve
                      </button>

                      <button
                        className="reject"
                        disabled={busy === event.id}
                        onClick={() => decide(event.id, 'reject')}
                      >
                        <X size={15} /> Reject
                      </button>
                    </div>
                  </article>
                ))
              ) : (
                <Empty text="No approval requests assigned to this account." />
              )}
            </Panel>
          )}

          {section === 'Calendar' && (
            <Panel title="Scheduled events">
              {loading ? (
                <Loading />
              ) : calendarEvents.length ? (
                calendarEvents.map((event, index) => (
                  <div className="row" key={event.id ?? index}>
                    <CalendarDays size={18} />

                    <div>
                      <b>{event.title || event.event_name || 'Campus event'}</b>

                      <small>
                        {fmt(event.start || event.event_date)}
                      </small>

                      <small style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '5px' }}>
                        <Clock3 size={14} />
                        {event.start && event.end
                          ? `${fmtTime(event.start)} – ${fmtTime(event.end)}`
                          : event.start_time && event.end_time
                            ? `${fmtTime(event.start_time)} – ${fmtTime(event.end_time)}`
                            : 'Timing unavailable'}
                      </small>
                    </div>
                  </div>
                ))
              ) : (
                <Empty text="Approved calendar events will appear here." />
              )}
            </Panel>
          )}

          {section === 'Venues' && (
            <Panel title="Campus venues">
              <div className="venue-grid">
                {venueList.map((venue) => (
                  <div className="venue" key={venue.id}>
                    <MapPin />
                    <h3>{venue.name}</h3>
                    <p>{venue.location || 'Campus location'}</p>
                    <small>Capacity: {venue.capacity}</small>
                  </div>
                ))}
              </div>

              {!venueList.length && (
                <Empty text="No venues returned by the API." />
              )}
            </Panel>
          )}

          {section === 'Notifications' && (
            <Panel title="Notifications">
              {notes.length ? (
                notes.map((note) => (
                  <div className="note" key={note.id}>
                    <b>{note.title || note.event_name || 'Event update'}</b>
                    <p>{note.message || 'There is an update on your event.'}</p>
                    <small>
                      {note.sent_at
                        ? new Date(note.sent_at).toLocaleString()
                        : 'Recent'}
                    </small>
                  </div>
                ))
              ) : (
                <Empty text="No notifications yet." />
              )}
            </Panel>
          )}

          <footer>
            © {new Date().getFullYear()} Eventify · Campus event management
          </footer>
        </div>
      </main>
    </div>
  );
}

function Stat({ label, n, icon: Icon }) {
  return (
    <article className="stat">
      <span><Icon size={19} /></span>
      <small>{label}</small>
      <strong>{n}</strong>
    </article>
  );
}

function Panel({ title, children, action }) {
  return (
    <section className="panel">
      <div className="panel-head">
        <h2>{title}</h2>
        {action && <button onClick={action}>View all →</button>}
      </div>
      {children}
    </section>
  );
}

function Event({ e }) {
  return (
    <div className="row">
      <span className="event-icon"><CalendarDays size={18} /></span>
      <div>
        <b>{e.event_name || 'Campus event'}</b>
        <small>
          {fmt(e.event_date)} · {e.start_time?.slice(0, 5) || 'Time TBD'} – {e.end_time?.slice(0, 5) || 'Time TBD'}
        </small>
      </div>
      <span className={`status ${String(e.status || 'pending').toLowerCase()}`}>
        {pretty(e.status)}
      </span>
    </div>
  );
}

function Empty({ text }) {
  return <div className="empty">{text}</div>;
}

function Loading() {
  return <div className="empty">Loading your workspace…</div>;
}
