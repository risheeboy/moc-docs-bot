/**
 * App Component
 * Root component for the chat widget
 */

import React, { useState } from 'react'
import { ChatWidget } from './components/ChatWidget'
import './styles/globals.css'

function App() {
  const [isOpen, setIsOpen] = useState(false)

  const handleToggle = () => {
    setIsOpen(!isOpen)
  }

  return (
    <div className="app-root">
      <ChatWidget isOpen={isOpen} onToggle={handleToggle} />
    </div>
  )
}

export default App
