'use client';

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { HardDrive, Cpu, Activity, Database } from 'lucide-react';
import { apiClient } from '@/lib/axios';

interface SystemHealth {
  status: string;
  database: string;
  scheduler: string;
  notifications: string;
  registered_scrapers: number;
  version: string;
  uptime_seconds: number;
  cpu_load: number[] | null;
  memory_usage_percent: number | null;
  disk_usage_percent: number | null;
  python_version: string;
  platform: string;
}

export default function AdminHealthPage() {
  const { data: health, isLoading } = useQuery<SystemHealth>({
    queryKey: ['admin', 'health'],
    queryFn: async () => {
      const res = await apiClient.get('/health');
      return res.data;
    },
    refetchInterval: 30000,
  });

  const getUptimeString = (seconds?: number) => {
    if (!seconds) return 'N/A';
    const days = Math.floor(seconds / 86400);
    const hrs = Math.floor((seconds % 86400) / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    
    if (days > 0) return `${days}d ${hrs}h`;
    return `${hrs}h ${mins}m`;
  };

  if (isLoading) {
    return <div className="p-8 text-center text-muted-foreground">Checking system health...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">System Health</h1>
        <Badge variant={health?.status === 'healthy' ? 'default' : 'destructive'} className="text-sm px-3 py-1 capitalize">
          {health?.status || 'Unknown'}
        </Badge>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Database className="h-5 w-5 text-blue-600" /> Database Connection
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <span>PostgreSQL / SQLAlchemy</span>
              <Badge variant={health?.database === 'connected' ? 'default' : 'destructive'} className="capitalize">
                {health?.database || 'Unknown'}
              </Badge>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Cpu className="h-5 w-5 text-amber-500" /> Host System
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Platform</span>
              <span className="font-medium">{health?.platform || 'Unknown'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">CPU Load (1,5,15m)</span>
              <span className="font-medium">
                {health?.cpu_load ? health.cpu_load.map(l => l.toFixed(2)).join(', ') : 'N/A'}
              </span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <HardDrive className="h-5 w-5 text-purple-500" /> Storage & Memory
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Disk Usage</span>
              <span className="font-medium">{health?.disk_usage_percent ? `${health.disk_usage_percent}%` : 'N/A'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Memory Usage</span>
              <span className="font-medium">{health?.memory_usage_percent ? `${health.memory_usage_percent.toFixed(1)}%` : 'N/A'}</span>
            </div>
          </CardContent>
        </Card>

        <Card className="lg:col-span-3">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5 text-primary" /> Application Environment
            </CardTitle>
            <CardDescription>FastAPI runtime configurations and worker stats.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="space-y-1">
                <span className="text-sm text-muted-foreground block">Version</span>
                <span className="font-medium block">{health?.version}</span>
              </div>
              <div className="space-y-1">
                <span className="text-sm text-muted-foreground block">Python Runtime</span>
                <span className="font-medium block">{health?.python_version || 'Unknown'}</span>
              </div>
              <div className="space-y-1">
                <span className="text-sm text-muted-foreground block">Uptime</span>
                <span className="font-medium block">{getUptimeString(health?.uptime_seconds)}</span>
              </div>
              <div className="space-y-1">
                <span className="text-sm text-muted-foreground block">Registered Scrapers</span>
                <span className="font-medium block">{health?.registered_scrapers} providers</span>
              </div>
              <div className="space-y-1">
                <span className="text-sm text-muted-foreground block">Scheduler Thread</span>
                <span className="font-medium block capitalize">
                  <Badge variant={health?.scheduler === 'running' ? 'outline' : 'secondary'} className="capitalize">{health?.scheduler}</Badge>
                </span>
              </div>
              <div className="space-y-1">
                <span className="text-sm text-muted-foreground block">Telegram Alerts</span>
                <span className="font-medium block capitalize">
                  <Badge variant={health?.notifications === 'enabled' ? 'outline' : 'secondary'} className="capitalize">{health?.notifications}</Badge>
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
