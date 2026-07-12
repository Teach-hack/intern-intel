import { NextResponse } from 'next/server';
import { cookies } from 'next/headers';
import { encryptSession } from '@/lib/session';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export async function POST(request: Request) {
  try {
    const body = await request.json();
    
    const response = await fetch(`${API_URL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username: body.email,
        password: body.password,
        device_name: 'Web Browser'
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(data, { status: response.status });
    }

    // Set refresh token in HttpOnly cookie
    const cookieStore = await cookies();
    cookieStore.set({
      name: 'refresh_token',
      value: data.refresh_token,
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: process.env.NODE_ENV === 'production' ? 'strict' : 'lax',
      path: '/',
      maxAge: 7 * 24 * 60 * 60, // 7 days
    });

    // Fetch user details to get role
    const meResponse = await fetch(`${API_URL}/auth/me`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${data.access_token}`
      }
    });

    let role = 'USER';
    if (meResponse.ok) {
      const meData = await meResponse.json();
      role = meData.role;
    }

    // Set signed session metadata cookie
    const sessionData = await encryptSession({ role });
    cookieStore.set({
      name: 'session_metadata',
      value: sessionData,
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: process.env.NODE_ENV === 'production' ? 'strict' : 'lax',
      path: '/',
      maxAge: 7 * 24 * 60 * 60, // 7 days
    });

    // Return only the access token and user info to the client
    return NextResponse.json({
      access_token: data.access_token,
      token_type: data.token_type,
      role: role
    });
  } catch {
    return NextResponse.json({ detail: 'Authentication failed' }, { status: 401 });
  }
}
