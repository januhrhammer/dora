/**
 * Main entry point for the Svelte application.
 *
 * This file initializes the Svelte app and mounts it to the DOM.
 * It imports the root App component and attaches it to the #app div in index.html.
 */

import App from './App.svelte'

const app = new App({
  target: document.getElementById('app')
})

export default app
