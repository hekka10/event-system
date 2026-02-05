import { Link, useNavigate } from "react-router-dom"

function Header() {
  const navigate = useNavigate();
  const user = JSON.parse(localStorage.getItem('user'));

  const handleLogout = () => {
    localStorage.removeItem('user');
    navigate('/login');
  };

  return (
    <header style={styles.header}>
      <h2 style={styles.logo}>SmartEvents</h2>
      <nav style={styles.nav}>
        <Link to="/" style={styles.link}>Home</Link>
        <Link to="/events" style={styles.link}>Events</Link>
        {user ? (
          <div style={styles.authGroup}>
            <span>{user.username}</span>
            <button onClick={handleLogout} style={styles.logoutBtn}>Logout</button>
          </div>
        ) : (
          <div style={styles.authGroup}>
            <Link to="/login" style={styles.link}>Login</Link>
            <Link to="/signup" style={styles.signupBtn}>Sign Up</Link>
          </div>
        )}
      </nav>
    </header>
  )
}

const styles = {
  header: {
    padding: "16px 40px",
    borderBottom: "1px solid #eee",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    backgroundColor: "#fff",
    position: "sticky",
    top: 0,
    zIndex: 1000
  },
  logo: {
    margin: 0,
    color: "#2563eb",
    fontWeight: "bold"
  },
  nav: {
    display: "flex",
    alignItems: "center",
    gap: "20px"
  },
  link: {
    textDecoration: "none",
    color: "#4b5563",
    fontWeight: "500"
  },
  authGroup: {
    display: "flex",
    alignItems: "center",
    gap: "15px"
  },
  signupBtn: {
    textDecoration: "none",
    backgroundColor: "#2563eb",
    color: "#fff",
    padding: "8px 20px",
    borderRadius: "8px",
    fontWeight: "600"
  },
  logoutBtn: {
    backgroundColor: "#fef2f2",
    color: "#dc2626",
    border: "1px solid #fee2e2",
    padding: "8px 16px",
    borderRadius: "8px",
    cursor: "pointer",
    fontWeight: "600"
  }
}

export default Header
