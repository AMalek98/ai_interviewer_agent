import React, { useState } from 'react'
import App from './App.jsx'
import OralInterview from './OralInterview.jsx'
import CodingInterviewer from './CodingInterviewer.jsx'

function Router() {
  const [selectedMode, setSelectedMode] = useState(null)

  if (selectedMode === 'text') {
    return <App onBack={() => setSelectedMode(null)} />
  }

  if (selectedMode === 'oral') {
    return <OralInterview onBack={() => setSelectedMode(null)} />
  }

  if (selectedMode === 'coding') {
    return <CodingInterviewer onBack={() => setSelectedMode(null)} />
  }

  // Selection Screen
  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #1e40af 0%, #3b82f6 100%)',
      padding: '2rem'
    }}>
      <div style={{
        background: 'white',
        borderRadius: '20px',
        padding: '3rem',
        boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
        maxWidth: '600px',
        width: '100%'
      }}>
        <h1 style={{
          fontSize: '2.5rem',
          marginBottom: '1rem',
          color: '#2d3748',
          textAlign: 'center'
        }}>
          🤖 AI Interview Assistant
        </h1>
        <p style={{
          fontSize: '1.1rem',
          color: '#718096',
          textAlign: 'center',
          marginBottom: '3rem'
        }}>
          Choose your interview type
        </p>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <button
            onClick={() => setSelectedMode('text')}
            style={{
              padding: '1.5rem',
              fontSize: '1.2rem',
              border: '2px solid #059669',
              borderRadius: '12px',
              background: 'white',
              color: '#059669',
              cursor: 'pointer',
              transition: 'all 0.3s',
              fontWeight: 'bold',
              boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
            }}
            onMouseEnter={(e) => {
              e.target.style.background = '#059669'
              e.target.style.color = 'white'
              e.target.style.transform = 'translateY(-2px)'
              e.target.style.boxShadow = '0 4px 12px rgba(5,150,105,0.3)'
            }}
            onMouseLeave={(e) => {
              e.target.style.background = 'white'
              e.target.style.color = '#059669'
              e.target.style.transform = 'translateY(0)'
              e.target.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)'
            }}
          >
            📝 Text-Based Interview
            <div style={{ fontSize: '0.9rem', fontWeight: 'normal', marginTop: '0.5rem', opacity: 0.8 }}>
              Traditional text Q&A with CV analysis
            </div>
          </button>

          <button
            onClick={() => setSelectedMode('oral')}
            style={{
              padding: '1.5rem',
              fontSize: '1.2rem',
              border: '2px solid #7c3aed',
              borderRadius: '12px',
              background: 'white',
              color: '#7c3aed',
              cursor: 'pointer',
              transition: 'all 0.3s',
              fontWeight: 'bold',
              boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
            }}
            onMouseEnter={(e) => {
              e.target.style.background = '#7c3aed'
              e.target.style.color = 'white'
              e.target.style.transform = 'translateY(-2px)'
              e.target.style.boxShadow = '0 4px 12px rgba(124,58,237,0.3)'
            }}
            onMouseLeave={(e) => {
              e.target.style.background = 'white'
              e.target.style.color = '#7c3aed'
              e.target.style.transform = 'translateY(0)'
              e.target.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)'
            }}
          >
            🎤 Oral Interview
            <div style={{ fontSize: '0.9rem', fontWeight: 'normal', marginTop: '0.5rem', opacity: 0.8 }}>
              Voice-based interview with speech recognition
            </div>
          </button>

          <button
            onClick={() => setSelectedMode('coding')}
            style={{
              padding: '1.5rem',
              fontSize: '1.2rem',
              border: '2px solid #16a34a',
              borderRadius: '12px',
              background: 'white',
              color: '#16a34a',
              cursor: 'pointer',
              transition: 'all 0.3s',
              fontWeight: 'bold',
              boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
            }}
            onMouseEnter={(e) => {
              e.target.style.background = '#16a34a'
              e.target.style.color = 'white'
              e.target.style.transform = 'translateY(-2px)'
              e.target.style.boxShadow = '0 4px 12px rgba(22,163,74,0.3)'
            }}
            onMouseLeave={(e) => {
              e.target.style.background = 'white'
              e.target.style.color = '#16a34a'
              e.target.style.transform = 'translateY(0)'
              e.target.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)'
            }}
          >
            💻 Coding Interview
            <div style={{ fontSize: '0.9rem', fontWeight: 'normal', marginTop: '0.5rem', opacity: 0.8 }}>
              Technical coding challenges with skill-based questions
            </div>
          </button>
        </div>

        <div style={{
          marginTop: '2rem',
          padding: '1rem',
          background: '#dbeafe',
          borderRadius: '8px',
          fontSize: '0.85rem',
          color: '#1e40af',
          border: '2px solid #3b82f6'
        }}>
          <strong>🚀 Unified Server:</strong> Run the new main.py for all interviews:
          <div style={{ marginTop: '0.5rem', fontFamily: 'monospace', background: '#1e293b', color: '#10b981', padding: '0.75rem', borderRadius: '6px', fontWeight: 'bold' }}>
            python backend/main.py
          </div>
          <ul style={{ marginTop: '0.75rem', marginLeft: '1.5rem', lineHeight: '1.8' }}>
            <li>✅ <strong>Text Interview</strong> → Available on port 5000</li>
            <li>✅ <strong>Oral Interview</strong> → Available on port 5000</li>
            <li>✅ <strong>Coding Interview</strong> → Available on port 5000</li>
          </ul>
        </div>
      </div>
    </div>
  )
}

export default Router
