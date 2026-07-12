'use client';

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ShieldCheck, HardDrive, Cpu, Activity } from 'lucide-react';
import { apiClient } from '@/lib/axios';

interface SystemHealth {
  status: string;
  database: string;
  scheduler: string;
  notifications: string;
  registered_scrapers: number;
  version: string;
  uptime_seconds: number;
}

export default function AdminHealthPage() {
  const { data: health, isLoading } = useQuery<SystemHealth>({
    queryKey: ['admin', 'health'],
    queryFn: async () => {
      const res = await apiClient.get('/health');
      return res.data;
    },
  });

  const getUptimeString = (seconds?: number) => {
    if (!seconds) return 'N/A';
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    return `${hrs}h ${mins}m`;
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">System Health</h1>
      </div>

      {isLoading ? (
        <div>Checking system health...</div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <ShieldCheck className="h-5 w-5 text-green-600" /> Database Connection
              </CardTitle>
              <CardDescription>Status of SQLAlchemy connection pool.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <span>Database Connectivity</span>
                <Badge variant={health?.database === 'connected' ? 'default' : 'destructive'}>
                  {health?.database}
                </Badge>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5 text-primary" /> Application Metrics
              </CardTitle>
              <CardDescription>FastAPI runtime configurations.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex justify-between border-b pb-2">
                <span className="text-muted-foreground">Version</span>
                <span>{health?.version}</span>
              </div>
              <div className="flex justify-between border-b pb-2">
                <span className="text-muted-foreground">Uptime</span>
                <span>{getUptimeString(health?.uptime_seconds)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Registered Scrapers</span>
                <span>{health?.registered_scrapers}</span>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
