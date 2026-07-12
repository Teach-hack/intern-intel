import React from 'react';
import Link from 'next/link';

export function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-muted/40">
      <div className="w-full max-w-md p-4 space-y-6">
        <div className="flex justify-center">
          <Link href="/" className="text-2xl font-bold tracking-tight text-primary">
            InternIntel
          </Link>
        </div>
        {children}
      </div>
    </div>
  );
}
