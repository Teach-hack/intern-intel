'use client';

import React, { use } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { MapPin, Building, Calendar, ExternalLink, ArrowLeft, Bookmark } from 'lucide-react';
import { userService } from '@/services/user.service';
import { internshipService } from '@/services/internship.service';
import { queryKeys } from '@/constants/queryKeys';
import { LoadingSkeleton } from '@/components/shared/LoadingSkeleton';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';

export default function InternshipDetailsPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const id = parseInt(resolvedParams.id, 10);
  const queryClient = useQueryClient();

  const { data: internship, isLoading, isError } = useQuery({
    queryKey: queryKeys.internships.detail(id),
    queryFn: () => internshipService.getInternship(id),
  });

  const { data: savedJobs, isLoading: isLoadingSaved } = useQuery({
    queryKey: ['savedJobs'],
    queryFn: () => userService.getSavedJobs(),
  });

  const isSaved = savedJobs?.some(job => job.internship_id === id) || false;

  const saveMutation = useMutation({
    mutationFn: () => userService.saveJob(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['savedJobs'] });
      toast.success('Internship saved to your profile.');
    },
    onError: () => {
      toast.error('Failed to save internship.');
    }
  });

  const removeMutation = useMutation({
    mutationFn: () => userService.removeSavedJob(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['savedJobs'] });
      toast.success('Internship removed from saved jobs.');
    },
    onError: () => {
      toast.error('Failed to remove internship.');
    }
  });

  const toggleSave = () => {
    if (isSaved) {
      removeMutation.mutate();
    } else {
      saveMutation.mutate();
    }
  };

  if (isLoading) return <LoadingSkeleton rows={8} />;
  if (isError || !internship) return <div className="text-center py-10">Failed to load internship details.</div>;

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center gap-4 mb-6">
        <Link href="/internships">
          <Button variant="outline" size="icon"><ArrowLeft className="h-4 w-4" /></Button>
        </Link>
        <h1 className="text-3xl font-bold tracking-tight">Internship Details</h1>
      </div>

      <Card>
        <CardHeader>
          <div className="flex justify-between items-start">
            <div>
              <CardTitle className="text-2xl">{internship.title}</CardTitle>
              <CardDescription className="text-lg mt-2 flex items-center gap-2">
                <Building className="h-4 w-4" /> {internship.company}
              </CardDescription>
            </div>
            <div className="flex gap-2">
              <Button 
                variant={isSaved ? "default" : "outline"} 
                size="icon"
                onClick={toggleSave}
                disabled={isLoadingSaved || saveMutation.isPending || removeMutation.isPending}
              >
                <Bookmark className={`h-4 w-4 ${isSaved ? 'fill-current' : ''}`} />
              </Button>
              <a href={internship.link} target="_blank" rel="noopener noreferrer">
                <Button><ExternalLink className="h-4 w-4 mr-2" /> Apply Now</Button>
              </a>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex flex-wrap gap-4">
            <Badge variant="secondary" className="flex items-center gap-1 text-sm py-1 px-3">
              <MapPin className="h-3 w-3" /> {internship.location}
            </Badge>
            {internship.is_remote && (
              <Badge variant="outline" className="text-sm py-1 px-3">Remote</Badge>
            )}
            <Badge variant="outline" className="text-sm py-1 px-3 capitalize">
              {internship.employment_type || 'Internship'}
            </Badge>
            {internship.date_posted && (
              <Badge variant="outline" className="flex items-center gap-1 text-sm py-1 px-3">
                <Calendar className="h-3 w-3" /> {new Date(internship.date_posted).toLocaleDateString()}
              </Badge>
            )}
            <Badge variant="default" className="text-sm py-1 px-3 capitalize bg-primary/20 text-primary hover:bg-primary/30">
              {internship.source}
            </Badge>
          </div>
          
          <div>
            <h3 className="font-semibold text-lg mb-2">Description</h3>
            <div className="prose dark:prose-invert max-w-none text-muted-foreground whitespace-pre-wrap">
              {internship.description || 'No description provided.'}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
