'use client';

import React from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Play, CheckCircle, XCircle, RefreshCw } from 'lucide-react';
import { toast } from 'sonner';
import { apiClient } from '@/lib/axios';

interface PipelineStatus {
  status: string;
  last_run: string;
  is_running: boolean;
  active_scrapers: string[];
}

export default function AdminPipelinePage() {
  const { data: status, isLoading, refetch } = useQuery<PipelineStatus>({
    queryKey: ['admin', 'pipeline', 'status'],
    queryFn: async () => {
      // Simulate status check or fetch from API
      return {
        status: 'idle',
        last_run: new Date().toISOString(),
        is_running: false,
        active_scrapers: ['greenhouse', 'lever', 'ashby'],
      };
    },
  });

  const runMutation = useMutation({
    mutationFn: async () => {
      await apiClient.post('/pipeline/run');
    },
    onSuccess: () => {
      toast.success('Sync pipeline triggered successfully');
      refetch();
    },
    onError: () => {
      toast.error('Failed to trigger sync pipeline');
    },
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Sync Pipeline</h1>
        <Button 
          disabled={runMutation.isPending || status?.is_running} 
          onClick={() => runMutation.mutate()}
          className="flex items-center gap-2"
        >
          <Play className="h-4 w-4" /> Run Pipeline
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Pipeline Status</CardTitle>
            <CardDescription>Current status of the aggregation pipeline.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex justify-between border-b pb-2">
              <span className="text-muted-foreground">State</span>
              <span className="font-semibold capitalize flex items-center gap-1.5">
                {status?.is_running ? (
                  <>
                    <RefreshCw className="h-4 w-4 animate-spin text-primary" /> Running
                  </>
                ) : (
                  <>
                    <CheckCircle className="h-4 w-4 text-green-600" /> Idle
                  </>
                )}
              </span>
            </div>
            <div className="flex justify-between border-b pb-2">
              <span className="text-muted-foreground">Last Executed</span>
              <span className="font-semibold">
                {status?.last_run ? new Date(status.last_run).toLocaleString() : 'Never'}
              </span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Registered Scrapers</CardTitle>
            <CardDescription>ATS providers currently connected.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {status?.active_scrapers.map((scraper) => (
                <span key={scraper} className="px-3 py-1 bg-muted rounded-md text-sm font-semibold capitalize">
                  {scraper}
                </span>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
