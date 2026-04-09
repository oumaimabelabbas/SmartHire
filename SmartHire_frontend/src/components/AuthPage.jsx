import { useEffect, useMemo, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { ROLE_VALUES } from '../constants/roles'

function AuthPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const params = useMemo(() => new URLSearchParams(location.search), [location.search])
  const initialMode = params.get('mode') === 'register' ? 'register' : 'login'
  const queryRole = params.get('role')
  const initialRole =
    queryRole === ROLE_VALUES.RECRUTEUR ? ROLE_VALUES.RECRUTEUR : ROLE_VALUES.CANDIDAT

  const [mode, setMode] = useState(initialMode)
  const [loginData, setLoginData] = useState({ username: '', password: '' })
  const [registerData, setRegisterData] = useState({
    username: '',
    email: '',
    role: initialRole,
    password: '',
    confirmPassword: '',
  })
  const [message, setMessage] = useState('')

  useEffect(() => {
    setMode(initialMode)
  }, [initialMode])

  useEffect(() => {
    setRegisterData((prev) => ({ ...prev, role: initialRole }))
  }, [initialRole])

  const updateQuery = (nextMode, nextRole = registerData.role) => {
    const nextParams = new URLSearchParams(location.search)
    nextParams.set('mode', nextMode)

    if (nextMode === 'register') {
      nextParams.set('role', nextRole)
    } else {
      nextParams.delete('role')
    }

    navigate(`/auth?${nextParams.toString()}`, { replace: true })
  }

  const handleModeChange = (nextMode) => {
    setMode(nextMode)
    setMessage('')
    updateQuery(nextMode)
  }

  const handleRegisterRoleChange = (nextRole) => {
    setRegisterData((prev) => ({ ...prev, role: nextRole }))
    setMessage('')
    updateQuery('register', nextRole)
  }

  const handleLoginSubmit = async (event) => {
    event.preventDefault()
    const { username, password } = loginData;
    if (!username.trim() || !password.trim()) {
      setMessage('Veuillez remplir username et password.')
      return
    }
    try {
    const res = await fetch("http://localhost:8086/Login", {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        username,
        password,
      }),
    });

    if (!res.ok) {
      throw new Error("Erreur lors de la connexion");
    }

    const data = await res.json();

    setMessage("Connexion réussie ");
    setLoginData({ username: '', password: '' })

      try {
    const mares = await fetch("http://localhost:8086/me", {
      method: "GET",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      }
    });

    if (!res.ok) {
      throw new Error("Erreur lors de l'inscription");
    }

    const user = await mares.json();
    if (user.role === ROLE_VALUES.CANDIDAT) {
      navigate("/candidat/dashboard");
    } else if (user.role === ROLE_VALUES.RECRUTEUR) {
      navigate("/recruteur/dashboard");
    } else {
      setMessage("Role utilisateur inconnu ");
    }

    
      

  } catch (err) {
    setMessage("Erreur serveur ");
    console.log(err)
  }


  } catch (err) {
    setMessage("Erreur serveur ");
    console.log(err)
  }
  }

  const handleRegisterSubmit = async (event) => {
    event.preventDefault()
    const { username, email, password, confirmPassword,role } = registerData

    if (!username.trim() || !email.trim() || !password.trim() || !confirmPassword.trim()) {
      setMessage('Tous les champs sont requis pour l\'inscription.')
      return
    }

    if (password !== confirmPassword) {
      setMessage('Le mot de passe et la confirmation ne correspondent pas.')
      return
    }

    try {
    const res = await fetch("http://localhost:8086/utilisateurs", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        username,
        email,
        password,
        role, 
      }),
    });

    if (!res.ok) {
      throw new Error("Erreur lors de l'inscription");
    }

    const data = await res.json();

    setMessage("Inscription réussie ");
    setRegisterData({
      username: '',
      email: '',  
      role: initialRole,
      password: '',
      confirmPassword: '',
    })

      


  } catch (err) {
    setMessage("Erreur serveur ");
    console.log(err)
  }
  }

  return (
    <main className="auth-page">
      <section className="auth-card">
        <div className="mode-row">
          <button
            className={mode === 'login' ? 'mode active' : 'mode'}
            onClick={() => handleModeChange('login')}
            type="button"
          >
            Se connecter
          </button>
          <button
            className={mode === 'register' ? 'mode active' : 'mode'}
            onClick={() => handleModeChange('register')}
            type="button"
          >
            S'inscrire
          </button>
        </div>

        {mode === 'login' ? (
          <form className="auth-form" onSubmit={handleLoginSubmit}>
            <label htmlFor="login-username">Username</label>
            <input
              id="login-username"
              type="text"
              value={loginData.username}
              onChange={(event) => setLoginData((prev) => ({ ...prev, username: event.target.value }))}
              placeholder="Votre username"
            />

            <label htmlFor="login-password">Password</label>
            <input
              id="login-password"
              type="password"
              value={loginData.password}
              onChange={(event) => setLoginData((prev) => ({ ...prev, password: event.target.value }))}
              placeholder="Votre password"
            />

            <button className="btn btn-submit" type="submit">
              Se connecter
            </button>
          </form>
        ) : (
          <form className="auth-form" onSubmit={handleRegisterSubmit}>
            <label>Choisir un role</label>
            <div className="register-role-switch" role="tablist" aria-label="Choisir le role">
              <button
                type="button"
                className={
                  registerData.role === ROLE_VALUES.CANDIDAT
                    ? 'register-role-btn active'
                    : 'register-role-btn'
                }
                onClick={() => handleRegisterRoleChange(ROLE_VALUES.CANDIDAT)}
              >
                Candidat
              </button>
              <button
                type="button"
                className={
                  registerData.role === ROLE_VALUES.RECRUTEUR
                    ? 'register-role-btn active'
                    : 'register-role-btn'
                }
                onClick={() => handleRegisterRoleChange(ROLE_VALUES.RECRUTEUR)}
              >
                Recruteur
              </button>
            </div>

            <label htmlFor="register-username">Username</label>
            <input
              id="register-username"
              type="text"
              value={registerData.username}
              onChange={(event) =>
                setRegisterData((prev) => ({ ...prev, username: event.target.value }))
              }
              placeholder="Votre username"
            />

            <label htmlFor="register-email">Email</label>
            <input
              id="register-email"
              type="email"
              value={registerData.email}
              onChange={(event) => setRegisterData((prev) => ({ ...prev, email: event.target.value }))}
              placeholder="Adresse email"
            />

            <label htmlFor="register-password">Password</label>
            <input
              id="register-password"
              type="password"
              value={registerData.password}
              onChange={(event) =>
                setRegisterData((prev) => ({ ...prev, password: event.target.value }))
              }
              placeholder="Creer un password"
            />

            <label htmlFor="register-confirm-password">Confirm password</label>
            <input
              id="register-confirm-password"
              type="password"
              value={registerData.confirmPassword}
              onChange={(event) =>
                setRegisterData((prev) => ({ ...prev, confirmPassword: event.target.value }))
              }
              placeholder="Confirmer le password"
            />

            <button className="btn btn-submit" type="submit">
              Creer un compte
            </button>
          </form>
        )}

        {message ? <p className="form-message">{message}</p> : null}
        <Link to="/" className="back-home">
          Retour a l'accueil
        </Link>
      </section>
    </main>
  )
}

export default AuthPage
