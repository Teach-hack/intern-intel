'use client';

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Briefcase, Building, Bookmark, CheckCircle, Activity, Info, Server, RefreshCw } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { dashboardService } from '@/services/dashboard.service';
import { DashboardResponse } from '@/types/dashboard';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';

export default function DashboardPage() {
  const { data, isLoading, isError, error, refetch, isRefetching } = useQuery<DashboardResponse>({
    queryKey: ['dashboardOverview'],
    queryFn: dashboardService.getOverview,
    refetchInterval: 60000, // Auto-refresh every minute
  });

  if (isLoading) {
    return <DashboardSkeleton />;
  }

  if (isError) {
    return (
      <div className="flex flex-col items-center justify-center space-y-4 h-[50vh]">
        <div className="p-4 rounded-full bg-destructive/10 text-destructive">
          <Activity className="h-10 w-10" />
        </div>
        <h2 className="text-xl font-semibold">Failed to load dashboard data</h2>
        <p className="text-muted-foreground">{error?.message || 'An unknown error occurred.'}</p>
        <Button onClick={() => refetch()} variant="outline">
          <RefreshCw className="mr-2 h-4 w-4" /> Try Again
        </Button>
      </div>
    );
  }

  if (!data) return null;

  // Format chart data
  const chartData = Object.entries(data.charts.source_distribution).map(([name, value]) => ({
    name,
    applications: value,
  }));

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <Button onClick={() => refetch()} variant="outline" size="sm" disabled={isRefetching}>
          <RefreshCw className={`mr-2 h-4 w-4 ${isRefetching ? 'animate-spin' : ''}`} /> 
          Refresh
        </Button>
      </div>
      
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatsCard title="Total Internships" value={data.overview.total_internships.toLocaleString()} icon={Briefcase} trend="Total in database" />
        <StatsCard title="New Today" value={data.overview.new_today.toLocaleString()} icon={CheckCircle} trend="Added in last 24h" />
        <StatsCard title="Companies" value={data.overview.companies.toLocaleString()} icon={Building} trend="Unique employers" />
        <StatsCard title="Saved Jobs" value={data.overview.saved_jobs.toLocaleString()} icon={Bookmark} trend="Your bookmarks" />
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <Card className="col-span-4">
          <CardHeader>
            <CardTitle>Jobs by Source</CardTitle>
          </CardHeader>
          <CardContent className="pl-2">
            <div className="h-[300px]">
              {chartData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#888888" opacity={0.2} />
                    <XAxis 
                      dataKey="name" 
                      stroke="#888888" 
                      fontSize={12} 
                      tickLine={false} 
                      axisLine={false} 
                    />
                    <YAxis 
                      stroke="#888888" 
                      fontSize={12} 
                      tickLine={false} 
                      axisLine={false} 
                      tickFormatter={(value) => `${value}`} 
                    />
                    <Tooltip cursor={{ fill: 'rgba(0,0,0,0.05)' }} contentStyle={{ borderRadius: '8px', border: '1px solid #eee' }} />
                    <Bar 
                      dataKey="applications" 
                      fill="hsl(var(--primary))" 
                      radius={[4, 4, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex h-full items-center justify-center text-muted-foreground">
                  No data available
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        <Card className="col-span-3">
          <CardHeader>
            <CardTitle>Recent Jobs</CardTitle>
          </CardHeader>
          <CardContent>
            {data.recent.internships.length > 0 ? (
              <div className="space-y-6">
                {data.recent.internships.map((job) => (
                  <div key={job.id} className="flex items-center">
                    <div className="ml-4 space-y-1">
                      <p className="text-sm font-medium leading-none line-clamp-1" title={job.title}>
                        {job.title}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        {job.company} • {new Date(job.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    <div className="ml-auto font-medium text-xs bg-primary/10 text-primary px-2 py-1 rounded">
                      {job.source}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex h-full min-h-[200px] flex-col items-center justify-center text-muted-foreground">
                <Info className="mb-2 h-8 w-8 opacity-20" />
                No recent jobs
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Server className="mr-2 h-5 w-5 text-muted-foreground" />
              System Information
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-muted-foreground">API Version</span>
                <span className="font-medium">{data.system.version}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Overall Health</span>
                <span className="font-medium text-green-600 capitalize">{data.system.health}</span>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Activity className="mr-2 h-5 w-5 text-muted-foreground" />
              Pipeline Status
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Current State</span>
                <span className="font-medium capitalize">{data.pipeline.status}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Last Execution</span>
                <span className="font-medium">
                  {data.pipeline.last_run ? new Date(data.pipeline.last_run).toLocaleString() : 'Never'}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

interface StatsCardProps {
  title: string;
  value: string | number;
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

function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <Skeleton className="h-9 w-[150px]" />
        <Skeleton className="h-9 w-[100px]" />
      </div>
      
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-4 w-4 rounded-full" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-8 w-16 mb-2" />
              <Skeleton className="h-3 w-32" />
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <Card className="col-span-4">
          <CardHeader>
            <Skeleton className="h-6 w-32" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-[300px] w-full" />
          </CardContent>
        </Card>
        
        <Card className="col-span-3">
          <CardHeader>
            <Skeleton className="h-6 w-32" />
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="flex items-center">
                  <div className="ml-4 space-y-2 w-full">
                    <Skeleton className="h-4 w-3/4" />
                    <Skeleton className="h-3 w-1/2" />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
      
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-48" />
          </CardHeader>
          <CardContent className="space-y-2">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-full" />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-48" />
          </CardHeader>
          <CardContent className="space-y-2">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-full" />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
