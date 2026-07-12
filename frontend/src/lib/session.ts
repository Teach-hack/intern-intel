import { SignJWT, jwtVerify } from 'jose';

const secretKey = process.env.SESSION_SECRET_KEY || 'intern-intel-super-secret-key-32-chars!!';
const key = new TextEncoder().encode(secretKey);

export async function encryptSession(payload: Record<string, unknown>) {
  return await new SignJWT(payload)
    .setProtectedHeader({ alg: 'HS256' })
    .setIssuedAt()
    .setExpirationTime('7d')
    .sign(key);
}

export async function decryptSession(input: string): Promise<Record<string, unknown>> {
  const { payload } = await jwtVerify(input, key, {
    algorithms: ['HS256'],
  });
  return payload;
}
