"use client";

import React, { useState, useEffect } from 'react';
import { getQwenServiceUrl, setQwenServiceUrl, testQwenServiceConnection } from '@/lib/api';

export default function QwenServiceConfigCard() {
  const [url, setUrl] = useState('');
  const [status, setStatus] = useState<'Not configured' | 'Connected' | 'Failed' | 'Model not loaded'>('Not configured');
  const [info, setInfo] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Backend is source of truth
    getQwenServiceUrl()
      .then(data => {
        if (data.url) {
          setUrl(data.url);
          localStorage.setItem('qwen_url', data.url);
        } else {
          const cached = localStorage.getItem('qwen_url');
          if (cached) setUrl(cached);
        }
      })
      .catch(err => console.warn("Could not fetch qwen url settings:", err.message || err));
  }, []);

  const handleSave = async () => {
    setLoading(true);
    try {
      await setQwenServiceUrl(url);
      localStorage.setItem('qwen_url', url);
      setStatus('Not configured');
      setInfo(null);
    } catch (e) {
      console.error(e);
      alert("Failed to save URL.");
    } finally {
      setLoading(false);
    }
  };

  const handleTestConnection = async () => {
    setLoading(true);
    try {
      const data = await testQwenServiceConnection();
      const isLoaded = data.model_loaded === true || String(data.model_loaded).toLowerCase() === 'true';
      const isNotLoaded = data.model_loaded === false || String(data.model_loaded).toLowerCase() === 'false';

      if (isLoaded) {
        setStatus('Connected');
        setInfo(`Device: ${data.device || 'N/A'}, Model: ${data.model_name || 'N/A'}`);
      } else if (isNotLoaded) {
        setStatus('Model not loaded');
        setInfo(data.startup_error || 'Service reachable but model not loaded');
      } else if (data.status === 'healthy') {
        setStatus('Connected');
        setInfo('Service is healthy (legacy connection)');
      } else {
        setStatus('Failed');
        setInfo('Unknown response format');
      }
    } catch (e: any) {
      const errStr = String(e.message || e);
      if (errStr.includes("model is not loaded")) {
        setStatus('Model not loaded');
      } else {
        setStatus('Failed');
      }
      setInfo(errStr);
    } finally {
      setLoading(false);
    }
  };

  const handleClear = async () => {
    setUrl('');
    localStorage.removeItem('qwen_url');
    setStatus('Not configured');
    setInfo(null);
    try {
      await setQwenServiceUrl('');
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="p-6 border rounded shadow-sm space-y-4 max-w-xl bg-white text-black">
      <h2 className="text-xl font-bold">Qwen GPU Service Configuration</h2>
      <div className="flex flex-col space-y-2">
        <label className="text-sm font-semibold">Service URL (Ngrok)</label>
        <input 
          type="text" 
          value={url} 
          onChange={(e) => setUrl(e.target.value)} 
          className="border border-gray-300 p-2 rounded text-black bg-gray-50 focus:ring-2 focus:ring-blue-500" 
          placeholder="https://your-ngrok-url.ngrok-free.dev"
        />
      </div>
      <div className="flex space-x-2">
        <button onClick={handleSave} disabled={loading} className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded font-medium disabled:opacity-50">Save URL</button>
        <button onClick={handleTestConnection} disabled={loading || !url} className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded font-medium disabled:opacity-50">Test Connection</button>
        <button onClick={handleClear} disabled={loading} className="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded font-medium disabled:opacity-50">Clear</button>
      </div>
      <div className="mt-4 flex items-center">
        <span className="font-semibold mr-2">Status:</span>
        <span className={`px-2 py-1 rounded text-sm font-bold ${status === 'Connected' ? 'bg-green-100 text-green-800' : status === 'Not configured' ? 'bg-gray-100 text-gray-800' : 'bg-red-100 text-red-800'}`}>
          {status}
        </span>
      </div>
      {info && (
        <div className="mt-2 text-sm text-gray-700 bg-gray-100 p-3 rounded break-all border border-gray-200">
          {info}
        </div>
      )}
    </div>
  );
}
