'use client';

import { useEffect } from 'react';
import { errorReporter } from '@/monitoring/errorReporter';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    errorReporter.report(error);
  }, [error]);

  return (
    <html>
      <body>
        <div style={{ padding: '2rem', textAlign: 'center', fontFamily: 'sans-serif' }}>
          <h2 style={{ fontSize: '1.5rem', marginBottom: '1rem' }}>Critical System Error</h2>
          <p style={{ color: '#666', marginBottom: '1.5rem' }}>
            A fatal error occurred at the root level.
          </p>
          <button 
            onClick={() => reset()}
            style={{ padding: '0.5rem 1rem', background: '#000', color: '#fff', borderRadius: '4px', cursor: 'pointer' }}
          >
            Try again
          </button>
        </div>
      </body>
    </html>
  );
}
