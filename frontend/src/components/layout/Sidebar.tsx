'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, Briefcase, Bookmark, Settings, Users, Activity, LogOut, Database, Server, Bell } from 'lucide-react';
import { cn } from '../../lib/utils';
import { useAuth } from '../../providers/auth-provider';
import { ROUTES } from '../../constants/routes';

const appNavigation = [
  { name: 'Dashboard', href: ROUTES.APP.DASHBOARD, icon: LayoutDashboard },
  { name: 'Internships', href: ROUTES.APP.INTERNSHIPS, icon: Briefcase },
  { name: 'Saved Jobs', href: ROUTES.APP.SAVED_JOBS, icon: Bookmark },
  { name: 'Profile', href: ROUTES.APP.PROFILE, icon: Settings },
];

const adminNavigation = [
  { name: 'Admin Dashboard', href: ROUTES.ADMIN.DASHBOARD, icon: Activity },
  { name: 'Users', href: ROUTES.ADMIN.USERS, icon: Users },
  { name: 'Sync Pipeline', href: ROUTES.ADMIN.PIPELINE, icon: Database },
  { name: 'Notifications', href: ROUTES.ADMIN.NOTIFICATIONS, icon: Bell },
  { name: 'System Health', href: ROUTES.ADMIN.HEALTH, icon: Server },
];

export function Sidebar({ isAdminView = false }: { isAdminView?: boolean }) {
  const pathname = usePathname();
  const { logout, user } = useAuth();
  
  const navigation = isAdminView ? adminNavigation : appNavigation;

  const finalNavigation = [...navigation];
  if (!isAdminView && user?.role === 'ADMIN') {
    finalNavigation.push({
      name: 'Admin Panel',
      href: ROUTES.ADMIN.DASHBOARD,
      icon: Activity
    });
  }

  return (
    <div className="flex h-full flex-col bg-card border-r w-64">
      <div className="p-6 flex items-center justify-between border-b">
        <Link href={ROUTES.APP.DASHBOARD} className="text-xl font-bold tracking-tight">
          InternIntel
        </Link>
      </div>
      <nav className="flex-1 space-y-1 px-4 py-6 overflow-y-auto">
        {finalNavigation.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                isActive
                  ? 'bg-primary text-primary-foreground'
                  : 'text-muted-foreground hover:bg-muted hover:text-foreground',
                'group flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors'
              )}
            >
              <item.icon
                className={cn(
                  isActive ? 'text-primary-foreground' : 'text-muted-foreground group-hover:text-foreground',
                  'mr-3 h-5 w-5 flex-shrink-0'
                )}
                aria-hidden="true"
              />
              {item.name}
            </Link>
          );
        })}
      </nav>
      <div className="p-4 border-t">
        <div className="flex items-center mb-4 px-2">
          <div className="ml-3">
            <p className="text-sm font-medium">{user?.username}</p>
            <p className="text-xs text-muted-foreground truncate">{user?.email}</p>
          </div>
        </div>
        <button
          onClick={() => logout()}
          className="flex w-full items-center px-3 py-2 text-sm font-medium text-red-600 hover:bg-red-50 hover:text-red-700 rounded-md transition-colors"
        >
          <LogOut className="mr-3 h-5 w-5" />
          Logout
        </button>
      </div>
    </div>
  );
}
