import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

// Retrieve the root HTML container element from index.html and mount the React application inside it.
// StrictMode triggers extra development-only checks to catch bugs early.
createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)

