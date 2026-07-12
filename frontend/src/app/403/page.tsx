import Link from 'next/link';

export default function ForbiddenPage() {
  return (
    <div className="flex h-screen w-full flex-col items-center justify-center bg-gray-50 dark:bg-gray-900 px-4">
      <div className="text-center">
        <h1 className="text-6xl font-bold text-red-500">403</h1>
        <h2 className="mt-4 text-2xl font-semibold text-gray-900 dark:text-white">Admin Access Required</h2>
        <p className="mt-2 text-gray-600 dark:text-gray-400 max-w-md mx-auto">
          You don&apos;t have permission to view this page. This area is restricted to administrators.
        </p>
        <div className="mt-8">
          <Link
            href="/dashboard"
            className="rounded-md bg-blue-600 px-6 py-3 text-sm font-semibold text-white shadow-sm hover:bg-blue-500 transition-colors"
          >
            Return to Dashboard
          </Link>
        </div>
      </div>
    </div>
  );
}
