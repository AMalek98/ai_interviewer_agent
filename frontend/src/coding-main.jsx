import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import CodingInterviewer from './CodingInterviewer.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <CodingInterviewer />
  </StrictMode>,
)