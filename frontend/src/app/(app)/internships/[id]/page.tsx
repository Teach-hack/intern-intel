'use client';

import React, { use } from 'react';
import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { MapPin, Building, Calendar, ExternalLink, ArrowLeft, Bookmark } from 'lucide-react';
import { internshipService } from '@/services/internship.service';
import { queryKeys } from '@/constants/queryKeys';
import { LoadingSkeleton } from '@/components/shared/LoadingSkeleton';
import { Badge } from '@/components/ui/badge';
import { Internship } from '@/types/internship';

export default function InternshipDetailsPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const id = parseInt(resolvedParams.id, 10);
  const [isSaved, setIsSaved] = React.useState(false);

  const { data: internship, isLoading, isError } = useQuery({
    queryKey: queryKeys.internships.detail(id),
    queryFn: () => internshipService.getInternship(id),
  });

  React.useEffect(() => {
    if (internship) {
      const timer = setTimeout(() => {
        const saved = localStorage.getItem('saved_jobs');
        if (saved) {
          try {
            const parsed = JSON.parse(saved) as Internship[];
            setIsSaved(parsed.some((job) => job.id === internship.id));
          } catch {
            // ignore
          }
        }
      }, 0);
      return () => clearTimeout(timer);
    }
  }, [internship]);

  const toggleSave = () => {
    if (!internship) return;
    const saved = localStorage.getItem('saved_jobs');
    let parsed: Internship[] = [];
    if (saved) {
      try {
        parsed = JSON.parse(saved);
      } catch {
        parsed = [];
      }
    }
    
    if (isSaved) {
      parsed = parsed.filter((job) => job.id !== internship.id);
      setIsSaved(false);
    } else {
      parsed.push(internship);
      setIsSaved(true);
    }
    localStorage.setItem('saved_jobs', JSON.stringify(parsed));
  };

  if (isLoading) return <LoadingSkeleton rows={8} />;
  if (isError || !internship) return <div>Failed to load internship details.</div>;

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
              {internship.employment_type}
            </Badge>
            {internship.date_posted && (
              <Badge variant="outline" className="flex items-center gap-1 text-sm py-1 px-3">
                <Calendar className="h-3 w-3" /> {new Date(internship.date_posted).toLocaleDateString()}
              </Badge>
            )}
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
