'use client';

import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ColumnDef } from '@tanstack/react-table';
import { Button } from '@/components/ui/button';
import { DataTable } from '@/components/shared/DataTable';
import { LoadingSkeleton } from '@/components/shared/LoadingSkeleton';
import { userService } from '@/services/user.service';
import { User } from '@/types/user';
import { toast } from 'sonner';

export default function AdminUsersPage() {
  const queryClient = useQueryClient();

  const { data: users, isLoading, isError } = useQuery({
    queryKey: ['admin', 'users'],
    queryFn: () => userService.getUsers(),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => userService.deleteUser(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
      toast.success('User deleted successfully');
    },
    onError: () => {
      toast.error('Failed to delete user');
    },
  });

  const columns: ColumnDef<User>[] = [
    {
      accessorKey: 'id',
      header: 'ID',
    },
    {
      accessorKey: 'username',
      header: 'Username',
      cell: ({ row }) => <span className="font-medium">{row.original.username}</span>,
    },
    {
      accessorKey: 'email',
      header: 'Email',
    },
    {
      accessorKey: 'role',
      header: 'Role',
      cell: ({ row }) => (
        <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${
          row.original.role === 'ADMIN' ? 'bg-primary/20 text-primary' : 'bg-muted text-muted-foreground'
        }`}>
          {row.original.role}
        </span>
      ),
    },
    {
      accessorKey: 'is_active',
      header: 'Active',
      cell: ({ row }) => (row.original.is_active ? 'Yes' : 'No'),
    },
    {
      id: 'actions',
      cell: ({ row }) => {
        const user = row.original;
        return (
          <Button
            variant="destructive"
            size="sm"
            onClick={() => {
              if (confirm(`Are you sure you want to delete ${user.username}?`)) {
                deleteMutation.mutate(user.id);
              }
            }}
            disabled={deleteMutation.isPending}
          >
            Delete
          </Button>
        );
      },
    },
  ];

  if (isError) return <div className="p-4 bg-destructive/10 text-destructive rounded-md">Failed to load users.</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Manage Users</h1>
      </div>

      {isLoading ? (
        <LoadingSkeleton rows={5} />
      ) : (
        <DataTable
          columns={columns}
          data={users || []}
          pageCount={1}
          currentPage={1}
          onPaginationChange={() => {}}
        />
      )}
    </div>
  );
}
