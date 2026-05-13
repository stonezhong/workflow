const MAIN_NAV_ITEMS = [
  { id: 'workflow-definitions', label: 'Workflow Definitions', icon: '⚙️' },
  { id: 'task-definitions',     label: 'Task Definitions',     icon: '📋' },
  { id: 'schemas',              label: 'Schemas',              icon: '{}' },
  { id: 'workflows',            label: 'Workflows',             icon: '▶️' },
]

const CREATE_NAV_ITEMS = [
  { id: 'new-task-definition',  label: 'New Task Definition',   icon: '+' },
  { id: 'new-workflow-definition', label: 'New Workflow Def', icon: '+' },
  { id: 'new-workflow',         label: 'New Workflow',          icon: '+' },
]

function SidebarItem({ item, activeView, onSelect }) {
  return (
    <li
      className={`sidebar-item${activeView === item.id ? ' active' : ''}`}
      onClick={() => onSelect(item.id)}
    >
      <span className="sidebar-icon">{item.icon}</span>
      {item.label}
    </li>
  )
}

export default function Sidebar({ activeView, onSelect, isOpen }) {
  return (
    <aside className={`sidebar${isOpen ? ' open' : ''}`}>
      <ul className="sidebar-nav">
        {MAIN_NAV_ITEMS.map(item => (
          <SidebarItem
            key={item.id}
            item={item}
            activeView={activeView}
            onSelect={onSelect}
          />
        ))}
      </ul>
      <div className="sidebar-divider" />
      <ul className="sidebar-nav">
        {CREATE_NAV_ITEMS.map(item => (
          <SidebarItem
            key={item.id}
            item={item}
            activeView={activeView}
            onSelect={onSelect}
          />
        ))}
      </ul>
    </aside>
  )
}
