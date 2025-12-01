<script>
/**
 * Login Component
 *
 * Simple login form for authentication.
 * Uses the authApi to login and stores the JWT token in localStorage.
 */

import { authApi } from './lib/api';

let username = '';
let password = '';
let error = '';
let loading = false;

/**
 * Handle login form submission
 */
async function handleLogin() {
  error = '';
  loading = true;

  try {
    await authApi.login(username, password);
    // Reload the page to trigger App.svelte to show the main app
    window.location.reload();
  } catch (err) {
    error = err.response?.data?.detail || 'Login fehlgeschlagen. Bitte überprüfen Sie Ihre Zugangsdaten.';
  } finally {
    loading = false;
  }
}
</script>

<main class="login-container">
  <div class="login-card">
    <h1>💊 Medikamenten-Tracker</h1>
    <p class="subtitle">Bitte melden Sie sich an</p>

    {#if error}
      <div class="error-message">
        {error}
      </div>
    {/if}

    <form on:submit|preventDefault={handleLogin}>
      <div class="form-group">
        <label for="username">Benutzername</label>
        <input
          id="username"
          type="text"
          bind:value={username}
          required
          disabled={loading}
          autocomplete="username"
        />
      </div>

      <div class="form-group">
        <label for="password">Passwort</label>
        <input
          id="password"
          type="password"
          bind:value={password}
          required
          disabled={loading}
          autocomplete="current-password"
        />
      </div>

      <button type="submit" class="btn-login" disabled={loading}>
        {loading ? 'Anmeldung läuft...' : 'Anmelden'}
      </button>
    </form>
  </div>
</main>

<style>
  .login-container {
    min-height: 100vh;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 1rem;
  }

  .login-card {
    background: white;
    border-radius: 16px;
    padding: 3rem 2.5rem;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
    max-width: 400px;
    width: 100%;
  }

  h1 {
    text-align: center;
    color: #333;
    margin: 0 0 0.5rem 0;
    font-size: 2rem;
  }

  .subtitle {
    text-align: center;
    color: #666;
    margin: 0 0 2rem 0;
  }

  .error-message {
    background: #fee;
    color: #c33;
    padding: 1rem;
    border-radius: 8px;
    margin-bottom: 1.5rem;
    border: 1px solid #fcc;
    font-size: 0.9rem;
  }

  .form-group {
    margin-bottom: 1.5rem;
  }

  label {
    display: block;
    margin-bottom: 0.5rem;
    color: #333;
    font-weight: 500;
    font-size: 0.95rem;
  }

  input {
    width: 100%;
    padding: 0.875rem;
    border: 2px solid #e0e0e0;
    border-radius: 8px;
    font-size: 1rem;
    transition: border-color 0.2s;
    font-family: inherit;
    box-sizing: border-box;
  }

  input:focus {
    outline: none;
    border-color: #667eea;
  }

  input:disabled {
    background: #f5f5f5;
    cursor: not-allowed;
  }

  .btn-login {
    width: 100%;
    padding: 1rem;
    background: #667eea;
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.2s;
  }

  .btn-login:hover:not(:disabled) {
    background: #5568d3;
  }

  .btn-login:disabled {
    background: #9faae8;
    cursor: not-allowed;
  }

  @media (max-width: 480px) {
    .login-card {
      padding: 2rem 1.5rem;
    }

    h1 {
      font-size: 1.75rem;
    }
  }
</style>
