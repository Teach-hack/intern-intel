'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Bell, Send } from 'lucide-react';
import { toast } from 'sonner';
import { apiClient } from '@/lib/axios';

export default function AdminNotificationsPage() {
  const triggerTestNotification = async () => {
    try {
      await apiClient.post('/notifications/test');
      toast.success('Test notification dispatched');
    } catch {
      toast.error('Failed to dispatch test notification');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Notification Channels</h1>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Telegram Channel</CardTitle>
            <CardDescription>System logs transmission settings.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between border-b pb-2">
              <span className="text-muted-foreground flex items-center gap-1.5">
                <Bell className="h-4 w-4 text-green-600" /> Channel Status
              </span>
              <span className="font-semibold text-green-600">Active</span>
            </div>
            <div className="pt-2">
              <Button onClick={triggerTestNotification} className="w-full flex items-center justify-center gap-2">
                <Send className="h-4 w-4" /> Trigger Test Notification
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
