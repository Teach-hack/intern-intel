import Link from 'next/link';

export default function UnauthorizedPage() {
  return (
    <div className="flex h-screen w-full flex-col items-center justify-center bg-gray-50 dark:bg-gray-900 px-4">
      <div className="text-center">
        <h1 className="text-6xl font-bold text-amber-500">401</h1>
        <h2 className="mt-4 text-2xl font-semibold text-gray-900 dark:text-white">Authentication Required</h2>
        <p className="mt-2 text-gray-600 dark:text-gray-400 max-w-md mx-auto">
          Please log in to access this page. Your session may have expired.
        </p>
        <div className="mt-8">
          <Link
            href="/login"
            className="rounded-md bg-blue-600 px-6 py-3 text-sm font-semibold text-white shadow-sm hover:bg-blue-500 transition-colors"
          >
            Go to Login
          </Link>
        </div>
      </div>
    </div>
  );
}
