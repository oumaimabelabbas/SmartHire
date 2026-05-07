import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { setCurrentCandidateScope } from '../utils/offers'

const PROFILE_API_URL = 'http://localhost:8086/profile'
const ME_API_URL = 'http://localhost:8086/me'

function normalizeUserPayload(rawUser) {
  const candidate = rawUser?.data ?? rawUser?.user ?? rawUser?.utilisateur ?? rawUser
  const source = candidate && typeof candidate === 'object' && !Array.isArray(candidate) ? candidate : rawUser ?? {}

  const resolvedEmail =
    source.email ??
    source.mail ??
    source.emailAddress ??
    rawUser?.email ??
    rawUser?.mail ??
    rawUser?.emailAddress ??
    rawUser?.user?.email ??
    rawUser?.utilisateur?.email ??
    rawUser?.data?.email ??
    ''

  return {
    ...source,
    nom: source.nom ?? '',
    prenom: source.prenom ?? '',
    username: source.username ?? source.login ?? '',
    email: resolvedEmail,
    role: source.role ?? '',
  }
}

function ProfilePage() {
  const [profile, setProfile] = useState(null)
  const [formData, setFormData] = useState({
    nom: '',
    prenom: '',
    username: '',
    email: '',
    password: '',
    role: '',
  })
  const [state, setState] = useState({ loading: true, saving: false, error: '', success: '' })

  useEffect(() => {
    const loadProfile = async () => {
      setState({ loading: true, saving: false, error: '', success: '' })

      try {
        const endpoints = [PROFILE_API_URL, ME_API_URL]
        let user = null

        for (const endpoint of endpoints) {
          const response = await fetch(endpoint, {
            method: 'GET',
            credentials: 'include',
          })

          if (!response.ok) {
            continue
          }

          user = normalizeUserPayload(await response.json())
          break
        }

        if (!user) {
          throw new Error('Session non valide. Connecte-toi pour voir ton profil.')
        }

        setCurrentCandidateScope(user)
        setProfile(user)
        setFormData({
          nom: user.nom,
          prenom: user.prenom,
          username: user.username,
          email: user.email,
          password: '',
          role: user.role,
        })
        setState({ loading: false, saving: false, error: '', success: '' })
      } catch (error) {
        console.error(error)
        setState({ loading: false, saving: false, error: error.message, success: '' })
      }
    }

    loadProfile()
  }, [])

  const handleChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setState((prev) => ({ ...prev, saving: true, error: '', success: '' }))

    const payload = {
      ...profile,
      nom: formData.nom.trim(),
      prenom: formData.prenom.trim(),
      username: formData.username.trim(),
      email: formData.email.trim(),
      role: formData.role || profile?.role,
      password: null,
    }

    if (formData.password.trim()) {
      payload.password = formData.password.trim()
    }

    try {
      const response = await fetch(PROFILE_API_URL, {
        method: 'PUT',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      })

      if (!response.ok) {
        const backendMessage = await response.text().catch(() => '')
        throw new Error(backendMessage || 'Erreur lors de la mise a jour du profil.')
      }

      const updated = normalizeUserPayload(await response.json())
      setCurrentCandidateScope(updated)
      setProfile(updated)
      setFormData((prev) => ({
        ...prev,
        nom: updated.nom || prev.nom,
        prenom: updated.prenom || prev.prenom,
        username: updated.username || prev.username,
        email: updated.email || prev.email,
        role: updated.role || prev.role,
        password: '',
      }))
      setState({ loading: false, saving: false, error: '', success: 'Profil mis a jour avec succes.' })
    } catch (error) {
      console.error(error)
      setState((prev) => ({ ...prev, saving: false, error: error.message, success: '' }))
    }
  }

  if (state.loading) {
    return (
      <main className="auth-page">
        <section className="auth-card">
          <p>Chargement du profil...</p>
        </section>
      </main>
    )
  }

  if (state.error && !profile) {
    return (
      <main className="auth-page">
        <section className="auth-card">
          <p className="candidate-v2-error">{state.error}</p>
          <Link to="/auth?mode=login" className="back-home">
            Se connecter
          </Link>
        </section>
      </main>
    )
  }

  return (
    <main className="auth-page">
      <section className="auth-card">
        <h2>Mon profil</h2>
        <form className="auth-form" onSubmit={handleSubmit}>
          <label htmlFor="profile-nom">Nom</label>
          <input
            id="profile-nom"
            type="text"
            value={formData.nom}
            onChange={(event) => handleChange('nom', event.target.value)}
          />

          <label htmlFor="profile-prenom">Prenom</label>
          <input
            id="profile-prenom"
            type="text"
            value={formData.prenom}
            onChange={(event) => handleChange('prenom', event.target.value)}
          />

          <label htmlFor="profile-username">Username</label>
          <input
            id="profile-username"
            type="text"
            value={formData.username}
            onChange={(event) => handleChange('username', event.target.value)}
            required
          />

          <label htmlFor="profile-email">Email</label>
          <input
            id="profile-email"
            type="email"
            value={formData.email}
            onChange={(event) => handleChange('email', event.target.value)}
            required
          />

          <label htmlFor="profile-password">Nouveau mot de passe (optionnel)</label>
          <input
            id="profile-password"
            type="password"
            value={formData.password}
            onChange={(event) => handleChange('password', event.target.value)}
            placeholder="Laisser vide pour garder le mot de passe actuel"
          />

          <label htmlFor="profile-role">Role</label>
          <input id="profile-role" type="text" value={formData.role} disabled />

          <button className="btn btn-submit" type="submit" disabled={state.saving}>
            {state.saving ? 'Mise a jour...' : 'Mettre a jour mon profil'}
          </button>
        </form>

        {state.error ? <p className="candidate-v2-error">{state.error}</p> : null}
        {state.success ? <p className="candidate-v2-success">{state.success}</p> : null}
      </section>
    </main>
  )
}

export default ProfilePage
