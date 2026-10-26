
import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../services/api';
import './Register.css';

function Register() {
  const navigate = useNavigate();

  const [clubs, setClubs] = useState([]);
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    department: '',
    club: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchClubs = async () => {
      try {
        const response = await api.get('clubs/');
        setClubs(Array.isArray(response.data) ? response.data : response.data.results || []);
      } catch {
        setError('Unable to load clubs. Please check that the backend is running.');
      }
    };

    fetchClubs();
  }, []);

  const handleChange = (event) => {
    const { name, value } = event.target;

    setFormData((previous) => ({
      ...previous,
      [name]: value,
    }));

    if (name === 'club') {
      const selectedClub = clubs.find(
        (item) => String(item.id) === value
      );

      setFormData((previous) => ({
        ...previous,
        club: value,
        department: selectedClub?.department || '',
      }));
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    if (formData.password.length < 8) {
      setError('Password must contain at least 8 characters.');
      return;
    }

    setLoading(true);

    try {
      await api.post('auth/register/', {
        username: formData.username.trim(),
        email: formData.email.trim(),
        password: formData.password,
        department: formData.department,
        club: Number(formData.club),
      });

      navigate('/login', {
        state: {
          message: 'Registration successful! Please log in.',
        },
      });
    } catch (err) {
      const data = err.response?.data;
      const message = data
        ? Object.entries(data)
            .map(([field, messages]) =>
              `${field}: ${Array.isArray(messages) ? messages.join(', ') : messages}`
            )
            .join(' ')
        : 'Registration failed. Please check your backend connection.';

      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="register-page">
      <div className="register-card">
        <div className="register-heading">
          <h1>Create Account</h1>
          <p>Join Eventify to manage and request campus events.</p>
        </div>

        {error && <div className="register-error">{error}</div>}

        <form onSubmit={handleSubmit}>
          <label htmlFor="username">Username</label>
          <input
            id="username"
            name="username"
            value={formData.username}
            onChange={handleChange}
            placeholder="Choose a username"
            autoComplete="username"
            required
          />

          <label htmlFor="email">Email</label>
          <input
            id="email"
            name="email"
            type="email"
            value={formData.email}
            onChange={handleChange}
            placeholder="Enter your email"
            autoComplete="email"
            required
          />

          <label htmlFor="club">Club</label>
          <select
            id="club"
            name="club"
            value={formData.club}
            onChange={handleChange}
            required
          >
            <option value="">Select your club</option>
            {clubs.map((club) => (
              <option key={club.id} value={club.id}>
                {club.name} — {club.department}
              </option>
            ))}
          </select>

          <label htmlFor="department">Department</label>
          <input
            id="department"
            name="department"
            value={formData.department}
            placeholder="Select a club first"
            readOnly
            required
          />

          <label htmlFor="password">Password</label>
          <input
            id="password"
            name="password"
            type="password"
            value={formData.password}
            onChange={handleChange}
            placeholder="At least 8 characters"
            autoComplete="new-password"
            minLength={8}
            required
          />

          <label htmlFor="confirmPassword">Confirm Password</label>
          <input
            id="confirmPassword"
            name="confirmPassword"
            type="password"
            value={formData.confirmPassword}
            onChange={handleChange}
            placeholder="Enter password again"
            autoComplete="new-password"
            required
          />

          <button type="submit" disabled={loading}>
            {loading ? 'Creating Account...' : 'Create Account'}
          </button>
        </form>

        <p className="register-login">
          Already have an account? <Link to="/login">Login</Link>
        </p>
      </div>
    </div>
  );
}

export default Register;
