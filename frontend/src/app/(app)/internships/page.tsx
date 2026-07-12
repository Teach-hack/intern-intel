'use client';

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ColumnDef } from '@tanstack/react-table';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { DataTable } from '@/components/shared/DataTable';
import { LoadingSkeleton } from '@/components/shared/LoadingSkeleton';
import { internshipService } from '@/services/internship.service';
import { Internship } from '@/types/internship';
import { queryKeys } from '@/constants/queryKeys';

export default function InternshipsPage() {
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);

  const { data, isLoading, isError } = useQuery({
    queryKey: queryKeys.internships.list({ page, page_size: pageSize }),
    queryFn: () => internshipService.getInternships({ page, page_size: pageSize }),
  });

  const columns: ColumnDef<Internship>[] = [
    {
      accessorKey: 'company',
      header: 'Company',
      cell: ({ row }) => <div className="font-semibold">{row.getValue('company')}</div>,
    },
    {
      accessorKey: 'title',
      header: 'Title',
    },
    {
      accessorKey: 'location',
      header: 'Location',
    },
    {
      accessorKey: 'is_remote',
      header: 'Remote',
      cell: ({ row }) => (row.getValue('is_remote') ? 'Yes' : 'No'),
    },
    {
      id: 'actions',
      cell: ({ row }) => {
        const internship = row.original;
        return (
          <Link href={`/internships/${internship.id}`}>
            <Button variant="outline" size="sm">View Details</Button>
          </Link>
        );
      },
    },
  ];

  if (isError) return <div>Failed to load internships.</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Internships</h1>
      </div>
      
      {isLoading ? (
        <LoadingSkeleton rows={10} />
      ) : (
        <DataTable 
          columns={columns} 
          data={data?.items || []} 
          pageCount={data?.pages || 0}
          currentPage={data?.page || 1}
          onPaginationChange={(newPage) => setPage(newPage)}
        />
      )}
    </div>
  );
}
