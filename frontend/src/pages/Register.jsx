import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { CalendarDays, ArrowRight } from 'lucide-react';
import { clubs, register } from '../services/api.js';

const roleOptions = [
  { value: 'STUDENT', label: 'Student' },
  { value: 'FACULTY_ADVISOR', label: 'Faculty Advisor' },
  { value: 'HOD', label: 'HOD' },
];

export default function Register() {
  const nav = useNavigate();
  const [c, C] = useState([]);
  const [f, F] = useState({ username: '', email: '', password: '', department: '', club: '', role: 'STUDENT' });
  const [e, E] = useState('');
  const [b, B] = useState(false);
  const [clubError, ClubError] = useState('');

  useEffect(() => {
    clubs().then(C).catch(() => ClubError('Could not load clubs. Start Django and try again.'));
  }, []);

  function change(event) {
    const { name, value } = event.target;
    if (name === 'club') {
      const selected = c.find(club => String(club.id) === value);
      F(current => ({ ...current, club: value, department: selected?.department || current.department }));
    } else {
      F(current => ({ ...current, [name]: value }));
    }
    E('');
  }

  async function submit(event) {
    event.preventDefault(); E(''); B(true);
    try {
      const payload = {
        username: f.username.trim(), email: f.email.trim(), password: f.password,
        department: f.department.trim(), role: f.role,
        club: f.club ? Number(f.club) : null,
      };
      await register(payload);
      nav('/login', { state: { registered: true, role: f.role } });
    } catch (error) {
      const data = error.response?.data;
      E(data ? Object.entries(data).map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(', ') : typeof value === 'object' ? JSON.stringify(value) : value}`).join(' · ') : 'Registration failed. Check backend connection and role registration permissions.');
    } finally { B(false); }
  }

  const staffRole = f.role !== 'STUDENT';
  return <main className="register-page">
    <header><Link className="brand" to="/login"><CalendarDays/> eventify<span>.</span></Link><small>CAMPUS EVENT PORTAL</small></header>
    <section className="register-card">
      <div className="kicker">GET STARTED</div><h1>Create your account</h1><p className="muted">Choose your role and join your campus community.</p>
      <form onSubmit={submit}>
        <label>Register as<select name="role" value={f.role} onChange={change} required>{roleOptions.map(role => <option value={role.value} key={role.value}>{role.label}</option>)}</select></label>
        {staffRole && <div className="hint">Faculty Advisor and HOD accounts must satisfy the server's club assignment and active-role rules. If your institution restricts staff registration, the backend may require an authorized invitation or administrator approval.</div>}
        <div className="two"><label>Username<input name="username" value={f.username} onChange={change} minLength="3" required placeholder="e.g. priya123"/></label><label>Email address<input name="email" type="email" value={f.email} onChange={change} required placeholder="you@college.edu"/></label></div>
        <label>Password<input name="password" type="password" value={f.password} onChange={change} minLength="8" required autoComplete="new-password" placeholder="At least 8 characters"/></label>
        <label>Club<select name="club" value={f.club} onChange={change} required><option value="">Choose your club</option>{c.map(club=><option key={club.id} value={club.id}>{club.name}</option>)}</select></label>
        <label>Department<input name="department" value={f.department} onChange={change} readOnly placeholder="Filled from your club"/></label>
        {clubError && <div className="error">{clubError}</div>}
        {e && <div className="error">{e}</div>}
        <button className="primary full" disabled={b || !c.length}>{b?'Creating account…':'Create '+roleOptions.find(r=>r.value===f.role).label+' account'} <ArrowRight size={17}/></button>
      </form>
      <p className="switch">Already registered? <Link to="/login">Sign in</Link></p>
    </section>
  </main>;
}
