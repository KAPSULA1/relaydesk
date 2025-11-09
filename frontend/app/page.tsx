'use client';
import { useEffect } from 'react';
import { motion } from 'framer-motion';
import { Loader2 } from 'lucide-react';
import { useUIStore } from '@/lib/stores/uiStore';

export default function Home() {
  const { theme } = useUIStore();

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      window.location.assign('/rooms');
    } else {
      window.location.assign('/login');
    }
  }, []);

  return (
    <div className={`min-h-screen flex items-center justify-center ${
      theme === 'dark' ? 'bg-gray-900' : 'bg-gray-50'
    }`}>
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="flex flex-col items-center gap-4"
      >
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl flex items-center justify-center"
        >
          <Loader2 className="w-8 h-8 text-white" />
        </motion.div>
        <motion.p
          animate={{ opacity: [0.5, 1, 0.5] }}
          transition={{ duration: 1.5, repeat: Infinity }}
          className={`text-xl font-medium ${
            theme === 'dark' ? 'text-white' : 'text-gray-900'
          }`}
        >
          Loading...
        </motion.p>
      </motion.div>
    </div>
  );
}
