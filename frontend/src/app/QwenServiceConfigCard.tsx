"use client";

import React, { useState, useEffect } from 'react';

export default function QwenServiceConfigCard() {
  const [url, setUrl] = useState('');
  const [status, setStatus] = useState<'Not configured' | 'Connected' | 'Failed' | 'Model not loaded'>('Not configured');
  const [info, setInfo] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Load existing URL from settings API on mount
    fetch('http://localhost:8000/api/v1/settings/qwen-service')
      .then(res => res.json())
      .then(data => {
        if (data.url) {
          setUrl(data.url);
          localStorage.setItem('qwen_url', data.url);
        }
      })
      .catch(err => console.error("Could not fetch initial qwen url settings", err));
  }, []);

  const handleSave = async () => {
    setLoading(true);
    try {
      await fetch('http://localhost:8000/api/v1/settings/qwen-service', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
      });
      localStorage.setItem('qwen_url', url);
      setStatus('Not configured'); // require re-test
      setInfo(null);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleTestConnection = async () => {
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/api/v1/settings/qwen-service/test', {
        method: 'POST',
      });
      
      const data = await res.json();
      
      if (!res.ok) {
        if (res.status === 503 || (data.detail && data.detail.includes("model is not loaded"))) {
           setStatus('Model not loaded');
        } else {
           setStatus('Failed');
        }
        setInfo(data.detail || 'Connection failed');
      } else {
        if (data.model_loaded) {
          setStatus('Connected');
          setInfo(`Device: ${data.device || 'N/A'}, Model: ${data.model_name || 'N/A'}`);
        } else {
          setStatus('Model not loaded');
          setInfo(data.startup_error || 'Service reachable but model not loaded');
        }
      }
    } catch (e) {
      setStatus('Failed');
      setInfo(String(e));
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
      await fetch('http://localhost:8000/api/v1/settings/qwen-service', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: '' })
      });
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="p-4 border rounded shadow-sm space-y-4 max-w-xl bg-white text-black">
      <h2 className="text-lg font-bold">Qwen GPU Service Configuration</h2>
      <div className="flex flex-col space-y-2">
        <label className="text-sm font-semibold">Service URL (Ngrok)</label>
        <input 
          type="text" 
          value={url} 
          onChange={(e) => setUrl(e.target.value)} 
          className="border p-2 rounded text-black" 
          placeholder="https://your-ngrok-url.ngrok-free.dev"
        />
      </div>
      <div className="flex space-x-2">
        <button onClick={handleSave} disabled={loading} className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded">Save URL</button>
        <button onClick={handleTestConnection} disabled={loading || !url} className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded">Test Connection</button>
        <button onClick={handleClear} disabled={loading} className="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded">Clear</button>
      </div>
      <div className="mt-4">
        <span className="font-semibold mr-2">Status:</span>
        <span className={`px-2 py-1 rounded text-sm ${status === 'Connected' ? 'bg-green-100 text-green-800' : status === 'Not configured' ? 'bg-gray-100 text-gray-800' : 'bg-red-100 text-red-800'}`}>
          {status}
        </span>
      </div>
      {info && (
        <div className="mt-2 text-sm text-gray-600 bg-gray-50 p-2 rounded break-all">
          {info}
        </div>
      )}
    </div>
  );
}
