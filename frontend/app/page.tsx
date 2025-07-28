'use client';

import { useEffect } from 'react';
import ApiTest from '../components/api-test';

export default function Home() {
  useEffect(() => {
    // Console log the public environment variable from Key Vault
    console.log('NEXT_PUBLIC_API_URL:', process.env.NEXT_PUBLIC_API_URL);
  }, []);

  return (
    <div className="min-h-screen p-8">
      <div className="max-w-6xl mx-auto">
        <header className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            justicetranscribe
          </h1>
          <p className="text-xl text-gray-600">
            Full-stack Next.js + FastAPI application with Azure AD authentication
          </p>
        </header>

        <main>
          <ApiTest />
        </main>

        <footer className="text-center mt-12 text-gray-500">
          <p>
            This application demonstrates Easy Auth integration between Next.js frontend 
            and FastAPI backend on Azure App Service.
          </p>
        </footer>
      </div>
    </div>
  );
}
