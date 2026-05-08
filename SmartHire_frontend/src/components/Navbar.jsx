import { useEffect, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import smartHireLogo from '../assets/smarthire-logo.png'
import { clearCurrentCandidateScope, setCurrentCandidateScope } from '../utils/offers'

const PROFILE_API_URL = 'http://localhost:8086/profile'
const ME_API_URL = 'http://localhost:8086/me'
const LOGOUT_API_URL = 'http://localhost:8086/logout'

function resolveRole(payload) {
  const role =
    payload?.role ?? payload?.authorities?.[0]?.authority ?? payload?.authorities?.[0] ?? ''

  if (typeof role === 'string') {
    return role
  }

  return ''
}

function Navbar() {
  const location = useLocation()
  const navigate = useNavigate()
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [userRole, setUserRole] = useState('')
  const isHomePage = location.pathname === '/'

  const handleLogout = async () => {
    try {
      await fetch(LOGOUT_API_URL, {
        method: 'POST',
        credentials: 'include',
      })
    } catch {
      // Even if backend logout fails, reset client state and redirect.
    }

    localStorage.setItem('smarthire-auth', 'false')
    clearCurrentCandidateScope()
    setIsLoggedIn(false)
    setUserRole('')
    navigate('/', { replace: true })
  }

  useEffect(() => {
    let isMounted = true

    const checkSession = async () => {
      const authFlag = localStorage.getItem('smarthire-auth')
      if (authFlag === 'false') {
        setIsLoggedIn(false)
        setUserRole('')
        return
      }

      try {
        const profileResponse = await fetch(PROFILE_API_URL, {
          method: 'GET',
          credentials: 'include',
        })

        if (!isMounted) {
          return
        }

        if (profileResponse.ok) {
          const profileUser = await profileResponse.json().catch(() => null)
          const role = resolveRole(profileUser)
          localStorage.setItem('smarthire-auth', 'true')
          setCurrentCandidateScope(profileUser)
          setIsLoggedIn(true)
          setUserRole(role)
          return
        }

        const meResponse = await fetch(ME_API_URL, {
          method: 'GET',
          credentials: 'include',
        })

        if (isMounted) {
          setIsLoggedIn(meResponse.ok)
          if (meResponse.ok) {
            const meUser = await meResponse.json().catch(() => null)
            localStorage.setItem('smarthire-auth', 'true')
            setCurrentCandidateScope(meUser)
            setUserRole(resolveRole(meUser))
          } else {
            localStorage.setItem('smarthire-auth', 'false')
            clearCurrentCandidateScope()
            setUserRole('')
          }
        }
      } catch {
        if (isMounted) {
          localStorage.setItem('smarthire-auth', 'false')
          clearCurrentCandidateScope()
          setIsLoggedIn(false)
          setUserRole('')
        }
      }
    }

    checkSession()

    return () => {
      isMounted = false
    }
  }, [location.pathname, location.search])

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
        {isHomePage ? (
          <nav className="menu-wrap" aria-label="Navigation principale">
            <a href="#about">A propos</a>
            <a href="#contact">Contact</a>
          </nav>
        ) : null}

        <div className="auth-wrap">
          {isLoggedIn ? (
            <>
              {userRole.includes('CANDIDAT') ? (
                <Link className="btn btn-light" to="/candidat/dashboard">
                  Dashboard Candidat
                </Link>
              ) : null}
              {userRole.includes('RECRUTEUR') ? (
                <Link className="btn btn-light" to="/recruteur/dashboard">
                  Dashboard Recruteur
                </Link>
              ) : null}

              <Link className="btn btn-dark" to="/profile">
                Voir mon profil
              </Link>

              <button type="button" className="btn btn-light" onClick={handleLogout}>
                Se deconnecter
              </button>
            </>
          ) : (
            <>
              <Link className="btn btn-light" to="/auth?mode=login">
                Se connecter
              </Link>
              <Link className="btn btn-dark" to="/auth?mode=register">
                S'inscrire
              </Link>
            </>
          )}
        </div>
      </div>
    </header>
  )
}

export default Navbar
