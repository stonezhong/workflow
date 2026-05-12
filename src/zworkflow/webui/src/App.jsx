import { useEffect, useState } from 'react'
import Sidebar from './components/Sidebar'
import WorkflowDefinitions from './components/WorkflowDefinitions'
import TaskDefinitions from './components/TaskDefinitions'
import Schemas from './components/Schemas'
import Workflows from './components/Workflows'
import NewWorkflow from './components/NewWorkflow'
import NewWorkflowDefinition from './components/NewWorkflowDefinition'
import NewTaskDefinition from './components/NewTaskDefinition'
import './App.css'

const VIEWS = {
  'workflow-definitions': 'Workflow Definitions',
  'task-definitions': 'Task Definitions',
  'schemas': 'Schemas',
  'workflows': 'Workflows',
  'new-workflow': 'New Workflow',
  'new-workflow-definition': 'New Workflow Definition',
  'new-task-definition': 'New Task Definition',
}

function App() {
  const options = Object.fromEntries(new URLSearchParams(window.location.hash.slice(1)));
  if (!('activeView' in options)) {
    // no activeView set, set to default
    options['activeView'] = 'workflow-definitions';
  }

  const [activeView, setActiveView] = useState(options['activeView'])
  const [sidebarOpen, setSidebarOpen] = useState(false)

  useEffect(() => {
    const handleHashChange = () => {
      const nextOptions = Object.fromEntries(new URLSearchParams(window.location.hash.slice(1)))
      setActiveView(nextOptions.activeView ?? 'workflow-definitions')
    }

    window.addEventListener('hashchange', handleHashChange)
    return () => window.removeEventListener('hashchange', handleHashChange)
  }, [])

  const handleSelect = (view) => {
    setActiveView(view)
    setSidebarOpen(false)
    window.location.hash = new URLSearchParams({ activeView: view }).toString();
  }

  const renderContent = () => {
    switch (activeView) {
      case 'workflow-definitions': return <WorkflowDefinitions />
      case 'task-definitions':     return <TaskDefinitions />
      case 'schemas':              return <Schemas />
      case 'workflows':            return <Workflows />
      case 'new-workflow':         return <NewWorkflow />
      case 'new-workflow-definition': return <NewWorkflowDefinition />
      case 'new-task-definition':  return <NewTaskDefinition />
      default:                     return null
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <button
          className="hamburger"
          onClick={() => setSidebarOpen(o => !o)}
          aria-label="Toggle navigation"
          aria-expanded={sidebarOpen}
        >
          <span /><span /><span />
        </button>
        <span className="app-title">ZWorkflow</span>
        <span className="view-label">{VIEWS[activeView]}</span>
      </header>

      <div className="app-body">
        {sidebarOpen && (
          <div className="sidebar-overlay" onClick={() => setSidebarOpen(false)} />
        )}
        <Sidebar
          activeView={activeView}
          onSelect={handleSelect}
          isOpen={sidebarOpen}
        />
        <main className="content">
          {renderContent()}
        </main>
      </div>
    </div>
  )
}

export default App
