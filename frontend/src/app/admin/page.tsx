'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Activity, Users, Database, Server } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function AdminDashboardPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Admin Dashboard</h1>
        <Button>Run Global Pipeline</Button>
      </div>
      
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatsCard title="System Health" value="100%" icon={Activity} trend="All systems operational" />
        <StatsCard title="Total Users" value="1,234" icon={Users} trend="+12 this week" />
        <StatsCard title="Active Scrapers" value="5" icon={Database} trend="3 running currently" />
        <StatsCard title="Database Size" value="2.4 GB" icon={Server} trend="Within limits" />
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Recent Pipeline Executions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="flex items-center justify-between border-b pb-4 last:border-0 last:pb-0">
                  <div className="space-y-1">
                    <p className="text-sm font-medium leading-none">Global Sync Pipeline</p>
                    <p className="text-sm text-muted-foreground">Executed by system</p>
                  </div>
                  <div className="font-medium text-sm text-green-600">Success</div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>System Logs (Tail)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 text-xs font-mono bg-muted p-4 rounded-md text-muted-foreground">
              <p>[INFO] Starting Workday scraper...</p>
              <p>[INFO] Found 45 new internships.</p>
              <p>[INFO] Workday scraper finished.</p>
              <p>[INFO] Starting Greenhouse scraper...</p>
              <p>[WARN] Rate limited on Lever, retrying...</p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

interface StatsCardProps {
  title: string;
  value: string;
  icon: React.ElementType;
  trend: string;
}

function StatsCard({ title, value, icon: Icon, trend }: StatsCardProps) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        <p className="text-xs text-muted-foreground">{trend}</p>
      </CardContent>
    </Card>
  );
}
