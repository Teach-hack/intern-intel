import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AppProviders } from "@/providers";
import { Toaster } from "@/components/ui/sonner";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "InternIntel | Automated Internship Search",
  description: "InternIntel aggregates, filters, and notifies you of the best internships from top companies globally.",
  openGraph: {
    title: "InternIntel | Automated Internship Search",
    description: "InternIntel aggregates, filters, and notifies you of the best internships from top companies globally.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <AppProviders>
          {children}
          <Toaster />
        </AppProviders>
      </body>
    </html>
  );
}
