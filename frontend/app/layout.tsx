import type { Metadata } from 'next';
import './globals.css';
import { Navbar } from '@/components/Navbar';
import { Sidebar } from '@/components/Sidebar';

export const metadata: Metadata = {
  title: 'GxP AI Co-Pilot | Continuous GxP IT Assurance | Novo Nordisk',
  description: 'Agentic AI Co-Pilot for Always-On, Audit-Ready GxP IT System Management',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="h-full bg-slate-50 antialiased">
      <body className="min-h-full flex flex-col font-sans bg-slate-50 text-slate-900 overflow-x-hidden">
        <Navbar />
        <div className="flex flex-1 min-h-0">
          <Sidebar />
          <main className="flex-1 p-5 md:p-6 overflow-y-auto w-full max-w-[1600px] mx-auto min-w-0">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
