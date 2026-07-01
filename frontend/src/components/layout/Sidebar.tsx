import { NavLink } from 'react-router-dom'
import {
  Shield, Activity, BarChart3, Siren, AlertTriangle,
  Brain, Settings, Users, LogOut, ChevronLeft,
  Network, FileText
} from 'lucide-react'
import { cn } from '@/utils/cn'
import { Button } from '@/components/ui/button'
import { useAuthStore } from '@/store/authStore'
import { useState } from 'react'

const navItems = [
  { to: '/dashboard', icon: Activity, label: 'Dashboard' },
  { to: '/packets', icon: Network, label: 'Live Packets' },
  { to: '/flows', icon: BarChart3, label: 'Network Flows' },
  { to: '/threats', icon: Siren, label: 'Threats' },
  { to: '/alerts', icon: AlertTriangle, label: 'Alerts' },
  { to: '/analytics', icon: BarChart3, label: 'Analytics' },
  { to: '/ml', icon: Brain, label: 'Machine Learning' },
  { to: '/users', icon: Users, label: 'Users' },
  { to: '/logs', icon: FileText, label: 'Logs' },
  { to: '/settings', icon: Settings, label: 'Settings' },
]

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false)
  const logout = useAuthStore((s) => s.logout)
  const user = useAuthStore((s) => s.user)

  return (
    <aside
      className={cn(
        'flex flex-col border-r border-border bg-sidebar transition-all duration-300',
        collapsed ? 'w-16' : 'w-64'
      )}
    >
      <div className="flex items-center gap-2 p-4 border-b border-border">
        <Shield className="h-8 w-8 text-primary flex-shrink-0" />
        {!collapsed && (
          <div className="flex flex-col">
            <span className="font-bold text-sm">AI-IDS</span>
            <span className="text-[10px] text-muted-foreground">Security Dashboard</span>
          </div>
        )}
      </div>

      <nav className="flex-1 p-2 space-y-1 overflow-y-auto">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors',
                isActive
                  ? 'bg-primary/10 text-primary font-medium'
                  : 'text-muted-foreground hover:bg-secondary hover:text-foreground'
              )
            }
          >
            <Icon className="h-4 w-4 flex-shrink-0" />
            {!collapsed && <span>{label}</span>}
          </NavLink>
        ))}
      </nav>

      <div className="p-2 border-t border-border">
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="flex items-center gap-3 px-3 py-2 w-full rounded-md text-sm text-muted-foreground hover:bg-secondary transition-colors"
        >
          <ChevronLeft className={cn('h-4 w-4 transition-transform', collapsed && 'rotate-180')} />
          {!collapsed && <span>Collapse</span>}
        </button>
      </div>

      <div className="p-2 border-t border-border">
        {!collapsed && user && (
          <div className="px-3 py-2 text-xs text-muted-foreground truncate">
            {user.email}
          </div>
        )}
        <Button variant="ghost" size="sm" className="w-full justify-start gap-3" onClick={logout}>
          <LogOut className="h-4 w-4" />
          {!collapsed && <span>Logout</span>}
        </Button>
      </div>
    </aside>
  )
}
