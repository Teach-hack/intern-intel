'use client';

import React, { useState, useEffect, Suspense } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ColumnDef } from '@tanstack/react-table';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { DataTable } from '@/components/shared/DataTable';
import { LoadingSkeleton } from '@/components/shared/LoadingSkeleton';
import { internshipService } from '@/services/internship.service';
import { Internship } from '@/types/internship';
import { Search } from 'lucide-react';

function InternshipsContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [page, setPage] = useState(Number(searchParams.get('page')) || 1);
  const [pageSize] = useState(10);
  
  const [searchInput, setSearchInput] = useState(searchParams.get('search') || '');
  const [companyInput, setCompanyInput] = useState(searchParams.get('company') || '');

  const search = searchParams.get('search') || '';
  const company = searchParams.get('company') || '';

  const updateQueryParams = (newParams: Record<string, string | number>) => {
    const current = new URLSearchParams(Array.from(searchParams.entries()));
    Object.entries(newParams).forEach(([key, value]) => {
      if (value) {
        current.set(key, String(value));
      } else {
        current.delete(key);
      }
    });
    router.push(`/internships?${current.toString()}`);
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    updateQueryParams({ search: searchInput, company: companyInput, page: 1 });
  };

  useEffect(() => {
    updateQueryParams({ page });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page]);

  const { data, isLoading, isError } = useQuery({
    queryKey: ['internships', { page, page_size: pageSize, search, company }],
    queryFn: () => {
      const params: Record<string, string | number> = { page, page_size: pageSize };
      if (search) params.search = search;
      if (company) params.company = company;
      return internshipService.getInternships(params);
    },
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

  if (isError) return (
    <div className="flex h-[50vh] flex-col items-center justify-center space-y-4">
      <div className="text-xl font-semibold">Failed to load internships.</div>
    </div>
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Internships</h1>
        
        <form onSubmit={handleSearch} className="flex w-full flex-col gap-2 md:w-auto md:flex-row md:items-center">
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              type="text"
              placeholder="Search title, skills..."
              className="w-full pl-8 md:w-[250px]"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
            />
          </div>
          <Input
            type="text"
            placeholder="Company"
            className="w-full md:w-[200px]"
            value={companyInput}
            onChange={(e) => setCompanyInput(e.target.value)}
          />
          <Button type="submit">Filter</Button>
        </form>
      </div>
      
      {isLoading ? (
        <LoadingSkeleton rows={10} />
      ) : (
        <DataTable 
          columns={columns} 
          data={data || []} 
          pageCount={data && data.length < pageSize ? page : undefined} 
          currentPage={page}
          onPaginationChange={(newPage) => setPage(newPage)}
        />
      )}
    </div>
  );
}

export default function InternshipsPage() {
  return (
    <Suspense fallback={<LoadingSkeleton rows={10} />}>
      <InternshipsContent />
    </Suspense>
  );
}
