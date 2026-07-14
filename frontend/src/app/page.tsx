"use client";

import { useEffect, useState } from 'react';
import { getHealth, getRouters } from '@/lib/api';
import { RouterInfo } from '@/types/router';

import QwenServiceConfigCard from '@/components/QwenServiceConfigCard';
import RouterPlayground from '@/components/RouterPlayground';
import RouterComparison from '@/components/RouterComparison';
import RouterEvaluation from '@/components/RouterEvaluation';

export default function Home() {
  const [healthStatus, setHealthStatus] = useState<string>('checking...');
  const [routers, setRouters] = useState<RouterInfo[]>([]);
  const [activeTab, setActiveTab] = useState<'qwen' | 'playground' | 'compare' | 'evaluation'>('qwen');

  useEffect(() => {
    async function init() {
      try {
        const health = await getHealth();
        setHealthStatus(health.status);
      } catch (e: any) {
        setHealthStatus('offline');
        console.error(e);
      }

      try {
        const routersList = await getRouters();
        setRouters(routersList);
      } catch (e: any) {
        console.error('Failed to load routers', e);
      }
    }
    init();
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 font-sans flex flex-col md:flex-row">
      {/* Sidebar */}
      <aside className="w-full md:w-64 bg-white border-r border-gray-200 flex-shrink-0 flex flex-col">
        <div className="p-6 border-b">
          <h1 className="text-2xl font-bold text-blue-700 leading-tight">Research Dashboard</h1>
          <p className="text-xs text-gray-500 mt-1">AI Tutor Routing</p>
        </div>
        
        <nav className="flex-1 p-4 space-y-2">
          <button 
            onClick={() => setActiveTab('qwen')}
            className={`w-full text-left px-4 py-3 rounded-lg font-medium transition-colors ${activeTab === 'qwen' ? 'bg-blue-50 text-blue-700' : 'text-gray-600 hover:bg-gray-100'}`}
          >
            Qwen Service Config
          </button>
          <button 
            onClick={() => setActiveTab('playground')}
            className={`w-full text-left px-4 py-3 rounded-lg font-medium transition-colors ${activeTab === 'playground' ? 'bg-blue-50 text-blue-700' : 'text-gray-600 hover:bg-gray-100'}`}
          >
            Router Playground
          </button>
          <button 
            onClick={() => setActiveTab('compare')}
            className={`w-full text-left px-4 py-3 rounded-lg font-medium transition-colors ${activeTab === 'compare' ? 'bg-blue-50 text-blue-700' : 'text-gray-600 hover:bg-gray-100'}`}
          >
            Router Comparison
          </button>
          {/* Evaluation preserved but hidden or low priority as requested */}
          <button 
            onClick={() => setActiveTab('evaluation')}
            className={`w-full text-left px-4 py-3 rounded-lg font-medium transition-colors ${activeTab === 'evaluation' ? 'bg-blue-50 text-blue-700' : 'text-gray-600 hover:bg-gray-100'}`}
          >
            Evaluation
          </button>
        </nav>
        
        <div className="p-4 border-t border-gray-200 text-sm">
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${healthStatus === 'ok' ? 'bg-green-500' : 'bg-red-500'}`}></div>
            <span className="text-gray-600">Backend: {healthStatus}</span>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 p-6 md:p-10 overflow-y-auto">
        <div className="max-w-6xl mx-auto">
          {activeTab === 'qwen' && (
            <div className="animate-in fade-in slide-in-from-bottom-2 duration-300">
               <h2 className="text-2xl font-bold mb-6 text-gray-800">Environment Setup</h2>
               <QwenServiceConfigCard />
            </div>
          )}
          
          {activeTab === 'playground' && (
            <div className="animate-in fade-in slide-in-from-bottom-2 duration-300">
               <RouterPlayground routers={routers} />
            </div>
          )}
          
          {activeTab === 'compare' && (
            <div className="animate-in fade-in slide-in-from-bottom-2 duration-300">
               <RouterComparison routers={routers} />
            </div>
          )}

          {activeTab === 'evaluation' && (
            <div className="animate-in fade-in slide-in-from-bottom-2 duration-300">
               <h2 className="text-2xl font-bold mb-6 text-gray-800">Dataset Evaluation</h2>
               <RouterEvaluation routers={routers} />
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
