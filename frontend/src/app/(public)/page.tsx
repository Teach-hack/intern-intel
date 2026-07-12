'use client';

import React from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { Search, Clock, Shield } from 'lucide-react';

const fadeIn = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 },
};

export default function LandingPage() {
  return (
    <div className="flex flex-col items-center">
      {/* Hero Section */}
      <section className="w-full py-24 lg:py-32 xl:py-48 flex justify-center text-center">
        <motion.div 
          className="container px-4 md:px-6"
          initial="hidden"
          animate="visible"
          variants={fadeIn}
          transition={{ duration: 0.5 }}
        >
          <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl md:text-6xl lg:text-7xl mb-6">
            Your Internship Search, <span className="text-primary">Automated.</span>
          </h1>
          <p className="mx-auto max-w-[700px] text-muted-foreground md:text-xl mb-8">
            Stop refreshing career pages. InternIntel aggregates, filters, and notifies you of the best internships from top companies globally.
          </p>
          <div className="flex flex-col sm:flex-row justify-center gap-4">
            <Link href="/register">
              <Button size="lg" className="w-full sm:w-auto font-semibold">Get Started for Free</Button>
            </Link>
            <Link href="/login">
              <Button size="lg" variant="outline" className="w-full sm:w-auto">Login to Dashboard</Button>
            </Link>
          </div>
        </motion.div>
      </section>

      {/* Features Section */}
      <section className="w-full py-20 bg-muted/30 flex justify-center">
        <div className="container px-4 md:px-6">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">Enterprise-Grade Features</h2>
            <p className="mt-4 text-muted-foreground">Everything you need to land your next role.</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            <FeatureCard 
              icon={<Search className="h-10 w-10 text-primary" />}
              title="Smart Aggregation"
              description="We scrape Workday, Greenhouse, Lever, and more in real-time."
            />
            <FeatureCard 
              icon={<Clock className="h-10 w-10 text-primary" />}
              title="Instant Alerts"
              description="Get notified the second a new internship is posted."
            />
            <FeatureCard 
              icon={<Shield className="h-10 w-10 text-primary" />}
              title="Verified Listings"
              description="No ghost jobs. Our pipelines verify every active listing."
            />
          </div>
        </div>
      </section>

      {/* ATS List Section */}
      <section className="w-full py-20 flex justify-center text-center border-t border-b">
        <div className="container px-4 md:px-6">
          <p className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-8">
            Supported Application Systems
          </p>
          <div className="flex flex-wrap justify-center gap-8 opacity-70 grayscale">
            {['Workday', 'Greenhouse', 'Lever', 'Ashby', 'iCIMS'].map((ats) => (
              <span key={ats} className="text-xl font-bold">{ats}</span>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}

function FeatureCard({ icon, title, description }: { icon: React.ReactNode, title: string, description: string }) {
  return (
    <motion.div 
      className="flex flex-col items-center text-center p-6 bg-card border rounded-2xl shadow-sm"
      whileHover={{ y: -5 }}
      transition={{ duration: 0.2 }}
    >
      <div className="mb-4 p-3 bg-primary/10 rounded-full">
        {icon}
      </div>
      <h3 className="text-xl font-semibold mb-2">{title}</h3>
      <p className="text-muted-foreground">{description}</p>
    </motion.div>
  );
}
