import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { decryptSession } from '@/lib/session';

export async function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Only protect /admin routes
  if (pathname.startsWith('/admin')) {
    const sessionCookie = request.cookies.get('session_metadata');
    
    if (!sessionCookie || !sessionCookie.value) {
      // Not logged in or no session, redirect to login
      const url = request.nextUrl.clone();
      url.pathname = '/login';
      return NextResponse.redirect(url);
    }

    try {
      const session = await decryptSession(sessionCookie.value);
      
      if (session.role !== 'ADMIN') {
        // Logged in but not admin
        const url = request.nextUrl.clone();
        url.pathname = '/dashboard';
        return NextResponse.redirect(url);
      }
    } catch (error) {
      // Invalid session cookie
      const url = request.nextUrl.clone();
      url.pathname = '/login';
      // Clear cookies if invalid
      const response = NextResponse.redirect(url);
      response.cookies.delete('session_metadata');
      response.cookies.delete('refresh_token');
      return response;
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/admin/:path*'],
};
