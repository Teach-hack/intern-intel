import { AdminLayout } from '@/components/layout/AdminLayout';
import { AdminGuard } from '@/components/shared/AdminGuard';

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <AdminGuard>
      <AdminLayout>{children}</AdminLayout>
    </AdminGuard>
  );
}
