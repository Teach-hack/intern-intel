'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { MapPin, Building, Trash2, ArrowRight } from 'lucide-react';
import { Internship } from '@/types/internship';

export default function SavedJobsPage() {
  const [savedJobs, setSavedJobs] = useState<Internship[]>([]);

  useEffect(() => {
    const timer = setTimeout(() => {
      const jobs = localStorage.getItem('saved_jobs');
      if (jobs) {
        try {
          setSavedJobs(JSON.parse(jobs));
        } catch {
          // Clear corrupt storage
          localStorage.removeItem('saved_jobs');
        }
      }
    }, 0);
    return () => clearTimeout(timer);
  }, []);

  const removeJob = (id: number) => {
    const updated = savedJobs.filter((job) => job.id !== id);
    setSavedJobs(updated);
    localStorage.setItem('saved_jobs', JSON.stringify(updated));
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Saved Jobs</h1>
      </div>

      {savedJobs.length === 0 ? (
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
          {savedJobs.map((job) => (
            <Card key={job.id} className="flex flex-col justify-between">
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
                    onClick={() => removeJob(job.id)}
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
          ))}
        </div>
      )}
    </div>
  );
}
