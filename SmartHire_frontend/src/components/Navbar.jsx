import { Link } from 'react-router-dom'
import smartHireLogo from '../assets/smarthire-logo.png'

function Navbar() {
  return (
    <header className="topbar">
      <div className="brand-wrap">
        <Link to="/" className="brand" aria-label="SmartHire accueil">
          <span className="brand-mark" aria-hidden="true">
            <img src={smartHireLogo} alt="" className="brand-logo" />
          </span>
          <span className="brand-name">
            Smart<span className="brand-hire">Hire</span>
          </span>
        </Link>
      </div>

      <div className="topbar-right">
        <nav className="menu-wrap" aria-label="Navigation principale">
          <a href="#about">A propos</a>
          <a href="#contact">Contact</a>
        </nav>

        <div className="auth-wrap">
          <Link className="btn btn-light" to="/auth?mode=login">
            Se connecter
          </Link>
          <Link className="btn btn-dark" to="/auth?mode=register">
            S'inscrire
          </Link>
        </div>
      </div>
    </header>
  )
}

export default Navbar
