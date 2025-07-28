/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable react/no-unescaped-entities */
'use client';

import { useState } from 'react';
import { apiClient } from '../lib/api-client';

export default function ApiTest() {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<Record<string, any>>({});
  const [error, setError] = useState<string | null>(null);

  const testEndpoint = async (name: string, apiCall: () => Promise<any>) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await apiCall();
      if (result.error) {
        throw new Error(result.error);
      }
      setResults(prev => ({
        ...prev,
        [name]: result.data
      }));
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : String(err);
      setError(`${name} failed: ${errorMessage}`);
      setResults(prev => ({
        ...prev,
        [name]: { error: errorMessage }
      }));
    } finally {
      setLoading(false);
    }
  };

  const testEndpoints = [
    { name: 'CORS Test', call: () => apiClient.testCors() },
    { name: 'Health Check', call: () => apiClient.getHealth() },
    { name: 'Root', call: () => apiClient.getRoot() },
    { name: 'User Profile', call: () => apiClient.getUserProfile() },
    { name: 'Current User', call: () => apiClient.getCurrentUser() },
    { name: 'All Users', call: () => apiClient.getUsers() },
    { name: 'Items', call: () => apiClient.getItems() },
  ];

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">API Authentication Test</h1>
      
      <div className="mb-6">
        <p className="text-gray-600 mb-4">
          This component tests the authenticated API endpoints. Start with the "CORS Test" 
          to verify cross-origin requests are working, then test the authenticated endpoints.
        </p>
        
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
        {testEndpoints.map((endpoint) => (
          <button
            key={endpoint.name}
            onClick={() => testEndpoint(endpoint.name, endpoint.call)}
            disabled={loading}
            className={`font-bold py-2 px-4 rounded ${
              endpoint.name === 'CORS Test' 
                ? 'bg-green-500 hover:bg-green-700 disabled:bg-gray-400' 
                : 'bg-blue-500 hover:bg-blue-700 disabled:bg-gray-400'
            } text-white`}
          >
            Test {endpoint.name}
          </button>
        ))}
      </div>

      <div className="space-y-4">
        {Object.entries(results).map(([name, result]) => (
          <div key={name} className="border rounded-lg p-4">
            <h3 className="font-semibold text-lg mb-2">{name} Response:</h3>
            <pre className="bg-gray-100 p-3 rounded text-sm overflow-x-auto">
              {JSON.stringify(result, null, 2)}
            </pre>
          </div>
        ))}
      </div>

      {loading && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
          <div className="bg-white p-4 rounded-lg">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
            <p className="mt-2">Loading...</p>
          </div>
        </div>
      )}
    </div>
  );
} 