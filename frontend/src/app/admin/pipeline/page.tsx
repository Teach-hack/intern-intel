'use client';

import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Play, CheckCircle, RefreshCw, Info } from 'lucide-react';
import { toast } from 'sonner';
import { apiClient } from '@/lib/axios';
import { Badge } from '@/components/ui/badge';

interface PipelineStatus {
  running: boolean;
  last_run: string | null;
  last_success: string | null;
  last_failure: string | null;
  duration: number | null;
  queue_length: number;
  currently_running_scrapers: string[];
  next_scheduled_run: string | null;
  scrapers_executed: number;
  jobs_discovered: number;
  jobs_inserted: number;
  jobs_updated: number;
  errors: number;
}

export default function AdminPipelinePage() {
  const queryClient = useQueryClient();

  const { data: status, isLoading, isError } = useQuery<PipelineStatus>({
    queryKey: ['admin', 'pipeline', 'status'],
    queryFn: async () => {
      const res = await apiClient.get('/pipeline/status');
      return res.data;
    },
    refetchInterval: 10000, // refresh every 10s
  });

  const runMutation = useMutation({
    mutationFn: async () => {
      const res = await apiClient.post('/pipeline/run');
      return res.data;
    },
    onSuccess: (data) => {
      toast.success(`Discovered: ${data.jobs_discovered}, Inserted: ${data.jobs_inserted}, Time: ${data.execution_time}s`);
      queryClient.invalidateQueries({ queryKey: ['admin', 'pipeline', 'status'] });
    },
    onError: (err: unknown) => {
      const errorMsg = err && typeof err === 'object' && 'response' in err && err.response && typeof err.response === 'object' && 'data' in err.response && err.response.data && typeof err.response.data === 'object' && 'detail' in err.response.data
        ? String((err as { response: { data: { detail: unknown } } }).response.data.detail)
        : (err instanceof Error ? err.message : 'Unknown error');
      toast.error(errorMsg);
    },
  });

  if (isLoading) {
    return <div className="p-8 text-center text-muted-foreground">Loading pipeline status...</div>;
  }

  if (isError) {
    return <div className="p-8 text-center text-destructive border rounded-lg m-6">Failed to load pipeline status</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <h1 className="text-3xl font-bold tracking-tight">Sync Pipeline</h1>
        <Button 
          disabled={runMutation.isPending || status?.running} 
          onClick={() => runMutation.mutate()}
          className="flex items-center gap-2"
        >
          {runMutation.isPending || status?.running ? (
            <RefreshCw className="h-4 w-4 animate-spin" />
          ) : (
            <Play className="h-4 w-4" />
          )}
          {status?.running ? 'Pipeline Running...' : 'Run Pipeline'}
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle>Pipeline State</CardTitle>
            <CardDescription>Current execution state and orchestration metrics.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-y-4 gap-x-8">
              <div className="flex justify-between border-b pb-2">
                <span className="text-muted-foreground">Status</span>
                <span className="font-semibold flex items-center gap-1.5">
                  {status?.running ? (
                    <Badge variant="default" className="flex items-center gap-1"><RefreshCw className="h-3 w-3 animate-spin" /> Running</Badge>
                  ) : (
                    <Badge variant="secondary" className="flex items-center gap-1"><CheckCircle className="h-3 w-3 text-green-600" /> Idle</Badge>
                  )}
                </span>
              </div>
              <div className="flex justify-between border-b pb-2">
                <span className="text-muted-foreground">Queue Length</span>
                <span className="font-medium">{status?.queue_length} tasks</span>
              </div>
              <div className="flex justify-between border-b pb-2">
                <span className="text-muted-foreground">Last Run</span>
                <span className="font-medium">
                  {status?.last_run ? new Date(status.last_run).toLocaleString() : 'Never'}
                </span>
              </div>
              <div className="flex justify-between border-b pb-2">
                <span className="text-muted-foreground">Next Scheduled Run</span>
                <span className="font-medium">
                  {status?.next_scheduled_run ? new Date(status.next_scheduled_run).toLocaleString() : 'Not scheduled'}
                </span>
              </div>
              <div className="flex justify-between border-b pb-2">
                <span className="text-muted-foreground">Last Success</span>
                <span className="font-medium text-green-600">
                  {status?.last_success ? new Date(status.last_success).toLocaleString() : 'Never'}
                </span>
              </div>
              <div className="flex justify-between border-b pb-2">
                <span className="text-muted-foreground">Last Failure</span>
                <span className="font-medium text-destructive">
                  {status?.last_failure ? new Date(status.last_failure).toLocaleString() : 'Never'}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Last Run Metrics</CardTitle>
            <CardDescription>Statistics from the most recent execution.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
             <div className="flex justify-between border-b pb-2">
                <span className="text-muted-foreground">Discovered</span>
                <span className="font-medium">{status?.jobs_discovered}</span>
              </div>
              <div className="flex justify-between border-b pb-2">
                <span className="text-muted-foreground">Inserted</span>
                <span className="font-medium text-green-600">+{status?.jobs_inserted}</span>
              </div>
              <div className="flex justify-between border-b pb-2">
                <span className="text-muted-foreground">Updated</span>
                <span className="font-medium text-blue-600">~{status?.jobs_updated}</span>
              </div>
              <div className="flex justify-between border-b pb-2">
                <span className="text-muted-foreground">Errors</span>
                <span className="font-medium text-destructive">{status?.errors}</span>
              </div>
          </CardContent>
        </Card>

        <Card className="lg:col-span-3">
          <CardHeader>
            <CardTitle>Active Scrapers</CardTitle>
            <CardDescription>Scrapers currently executing or registered for the next run.</CardDescription>
          </CardHeader>
          <CardContent>
            {status?.currently_running_scrapers && status.currently_running_scrapers.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {status.currently_running_scrapers.map((scraper) => (
                  <span key={scraper} className="px-3 py-1 bg-primary/10 text-primary rounded-full text-sm font-semibold capitalize flex items-center gap-2">
                    <RefreshCw className="h-3 w-3 animate-spin" /> {scraper}
                  </span>
                ))}
              </div>
            ) : (
              <div className="flex items-center gap-2 text-muted-foreground">
                <Info className="h-4 w-4" /> No scrapers currently active. Total {status?.scrapers_executed} scrapers executed in last run.
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
