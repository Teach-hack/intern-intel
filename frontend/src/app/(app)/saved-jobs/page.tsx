'use client';

import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import Link from 'next/link';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { MapPin, Building, Trash2, ArrowRight } from 'lucide-react';
import { userService } from '@/services/user.service';
import { LoadingSkeleton } from '@/components/shared/LoadingSkeleton';
import { toast } from 'sonner';

export default function SavedJobsPage() {
  const queryClient = useQueryClient();

  const { data: savedJobs, isLoading, isError } = useQuery({
    queryKey: ['savedJobs'],
    queryFn: () => userService.getSavedJobs(),
  });

  const removeMutation = useMutation({
    mutationFn: (internshipId: number) => userService.removeSavedJob(internshipId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['savedJobs'] });
      toast.success('Internship removed from saved jobs.');
    },
    onError: () => {
      toast.error('Failed to remove internship.');
    }
  });

  if (isLoading) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-bold tracking-tight">Saved Jobs</h1>
        <div className="grid gap-4 md:grid-cols-2">
           {[1, 2, 3, 4].map(i => (
             <Card key={i} className="h-48">
               <CardContent className="p-6">
                 <LoadingSkeleton rows={4} />
               </CardContent>
             </Card>
           ))}
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-bold tracking-tight">Saved Jobs</h1>
        <div className="flex flex-col items-center justify-center p-10 text-center border rounded-lg text-destructive">
          Failed to load saved jobs.
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Saved Jobs</h1>
      </div>

      {!savedJobs || savedJobs.length === 0 ? (
        <Card className="border-dashed py-12">
          <CardContent className="flex flex-col items-center justify-center text-center space-y-4">
            <div className="rounded-full bg-muted p-4">
              <Building className="h-8 w-8 text-muted-foreground" />
            </div>
            <div className="space-y-2">
              <h3 className="font-semibold text-lg">No saved jobs yet</h3>
              <p className="text-sm text-muted-foreground max-w-sm">
                Explore available internships and save the ones you are interested in.
              </p>
            </div>
            <Link href="/internships">
              <Button>Browse Internships</Button>
            </Link>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {savedJobs.map((savedJob) => {
            const job = savedJob.internship;
            return (
              <Card key={savedJob.id} className="flex flex-col justify-between">
                <CardHeader className="pb-4">
                  <div className="flex justify-between items-start gap-4">
                    <div>
                      <CardTitle className="text-lg line-clamp-1">{job.title}</CardTitle>
                      <CardDescription className="flex items-center gap-1.5 mt-1">
                        <Building className="h-4 w-4" /> {job.company}
                      </CardDescription>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="text-muted-foreground hover:text-destructive shrink-0"
                      onClick={() => removeMutation.mutate(job.id)}
                      disabled={removeMutation.isPending}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex flex-wrap gap-2">
                    <Badge variant="secondary" className="flex items-center gap-1">
                      <MapPin className="h-3 w-3" /> {job.location}
                    </Badge>
                    {job.is_remote && (
                      <Badge variant="outline">Remote</Badge>
                    )}
                  </div>
                  <div className="flex justify-end gap-2 pt-2">
                    <Link href={`/internships/${job.id}`} className="w-full">
                      <Button variant="outline" className="w-full">
                        View Details <ArrowRight className="h-4 w-4 ml-2" />
                      </Button>
                    </Link>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
