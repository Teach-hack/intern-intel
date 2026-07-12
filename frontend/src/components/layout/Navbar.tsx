'use client';

import React from 'react';
import { Menu } from 'lucide-react';
import { Button } from '../ui/button';

interface NavbarProps {
  onMenuClick?: () => void;
  title?: string;
}

export function Navbar({ onMenuClick, title }: NavbarProps) {
  return (
    <header className="flex h-16 shrink-0 items-center gap-x-4 border-b bg-background px-4 shadow-sm sm:gap-x-6 sm:px-6 lg:px-8">
      <Button variant="ghost" size="icon" className="-m-2.5 p-2.5 text-muted-foreground lg:hidden" onClick={onMenuClick}>
        <span className="sr-only">Open sidebar</span>
        <Menu className="h-6 w-6" aria-hidden="true" />
      </Button>
      <div className="flex flex-1 gap-x-4 self-stretch lg:gap-x-6 items-center">
        <div className="flex-1">
          {title && <h1 className="text-xl font-semibold tracking-tight">{title}</h1>}
        </div>
      </div>
    </header>
  );
}
