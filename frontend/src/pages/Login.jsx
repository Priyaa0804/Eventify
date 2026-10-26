import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { CalendarDays, ArrowRight, Eye, EyeOff, GraduationCap, UserCheck, ShieldCheck } from 'lucide-react';
import { login, me } from '../services/api.js';

const roles = [
  { value: 'STUDENT', label: 'Student', icon: GraduationCap },
  { value: 'FACULTY_ADVISOR', label: 'Faculty Advisor', icon: UserCheck },
  { value: 'HOD', label: 'HOD', icon: ShieldCheck },
];
const roleLabel = value => roles.find(role => role.value === value)?.label || value;

export default function Login() {
  const nav = useNavigate();
  const [role, setRole] = useState('STUDENT');
  const [u, U] = useState('');
  const [p, P] = useState('');
  const [show, S] = useState(false);
  const [busy, B] = useState(false);
  const [err, E] = useState('');

  async function submit(e) {
    e.preventDefault(); B(true); E('');
    try {
      await login(u.trim(), p);
      const user = await me();
      const actualRole = String(user.role || user.user_role || '').toUpperCase();
      if (actualRole !== role) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('current_user');
        E(`This account is registered as ${roleLabel(actualRole)}. Select the matching role to sign in.`);
        return;
      }
      localStorage.setItem('current_user', JSON.stringify(user));
      nav('/dashboard', { replace: true });
    } catch (x) {
      E(x.response?.data?.detail || 'Login failed. Check your username, password, selected role, and Django connection.');
    } finally { B(false); }
  }

  return <main className="auth">
    <section className="hero"><Link className="brand" to="/login"><CalendarDays/> eventify<span>.</span></Link><div className="hero-copy"><small>CAMPUS EVENTS, SIMPLIFIED</small><h1>Great events<br/>start <em>here.</em></h1><p>Plan campus experiences, coordinate teams and move every event forward — all in one place.</p></div><footer>Made for students. Ready for campus.</footer><i className="orb"/></section>
    <section className="auth-side"><div className="form"><Link className="mobile-brand" to="/login"><CalendarDays/> eventify<span>.</span></Link><small className="kicker">WELCOME BACK</small><h2>Sign in to Eventify</h2><p className="muted">Choose your role to open the right campus workspace.</p>
      <form onSubmit={submit}>
        <label>Login as<select value={role} onChange={e => { setRole(e.target.value); E(''); }} required>{roles.map(r => <option value={r.value} key={r.value}>{r.label}</option>)}</select></label>
        <label>Username<input autoComplete="username" value={u} onChange={e=>U(e.target.value)} placeholder="Enter your username" required/></label>
        <label>Password<div className="password"><input type={show?'text':'password'} autoComplete="current-password" value={p} onChange={e=>P(e.target.value)} placeholder="Enter your password" required/><button type="button" onClick={()=>S(!show)} aria-label="Toggle password">{show?<EyeOff size={18}/>:<Eye size={18}/>}</button></div></label>
        {err&&<div className="error">{err}</div>}
        <button className="primary full" disabled={busy}>{busy?'Signing in…':'Sign in as '+roleLabel(role)} <ArrowRight size={17}/></button>
      </form>
      <p className="switch">New to Eventify? <Link to="/register">Create an account</Link></p>
    </div></section>
  </main>;
}
