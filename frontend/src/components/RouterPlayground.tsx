"use client";

import React, { useState } from 'react';
import { routeQuestion, getQwenServiceUrl } from '@/lib/api';
import { HybridConfig, QuickTestScenario, RouterInfo, RouteResponse } from '@/types/router';
import RouterResultCard from './RouterResultCard';
import HybridConfigPanel from './HybridConfigPanel';
import QuickTestScenarios from './QuickTestScenarios';

interface Props {
  routers: RouterInfo[];
  hybridConfig: HybridConfig;
  onHybridConfigChange: (config: HybridConfig) => void;
}

export default function RouterPlayground({ routers, hybridConfig, onHybridConfigChange }: Props) {
  const [selectedRouter, setSelectedRouter] = useState<string>('rule_v2');
  const [question, setQuestion] = useState('');
  const [history, setHistory] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<RouteResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleRun = async () => {
    if (!question.trim()) {
      setError('Vui lòng nhập câu hỏi');
      return;
    }
    
    if (selectedRouter === 'qwen_v0') {
       try {
         const config = await getQwenServiceUrl();
         if (!config.url) {
            setError('Qwen GPU Service URL is not configured. Please configure it in the settings tab.');
            return;
         }
       } catch (e) {
         // Allow backend to fail with 500/503
       }
    }

    setLoading(true);
    setError(null);
    setResult(null);

    const historyArray = history.split('\n').map(s => s.trim()).filter(s => s.length > 0);

    try {
      const res = await routeQuestion({
        router_id: selectedRouter,
        question: question,
        history: historyArray,
        hybrid_config: selectedRouter === 'hybrid' ? hybridConfig : undefined,
      });
      setResult(res);
    } catch (e: any) {
      setError(e.message || String(e));
    } finally {
      setLoading(false);
    }
  };

  const handleScenarioSelect = (scenario: QuickTestScenario) => {
    setQuestion(scenario.question);
    setHistory(scenario.history.join('\n'));
    setResult(null);
    setError(null);
  };

  const currentRouterName = routers.find(r => r.id === selectedRouter)?.name || selectedRouter;

  return (
    <div className="flex flex-col md:flex-row gap-8">
      <div className="w-full md:w-1/2 space-y-5">
        <h2 className="text-2xl font-bold text-gray-800 border-b pb-2">Router Playground</h2>
        
        <div>
          <label className="block text-sm font-semibold mb-2 text-gray-700">Select Router</label>
          <select 
            className="w-full border border-gray-300 rounded-md p-2.5 bg-white text-gray-800 shadow-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
            value={selectedRouter}
            onChange={(e) => setSelectedRouter(e.target.value)}
          >
            {routers.length > 0 ? routers.map(r => (
              <option 
                key={r.id} 
                value={r.id} 
                disabled={r.available === false || r.status === 'unavailable'}
              >
                {r.name}{r.available === false || r.status === 'unavailable' ? ` (${r.unavailable_reason ?? 'unavailable'})` : ''}
              </option>
            )) : (
              <>
                 <option value="rule_v2">Rule-based Router V2</option>
                 <option value="qwen_v0">Qwen Router V0 (GPU Service)</option>
                 <option value="llm_deepseek_v0">LLM Router DeepSeek V0</option>
                 <option value="llm_gemini_v0">LLM Router Gemini V0</option>
                 <option value="llm_openai_v0">LLM Router OpenAI V0</option>
                 <option value="hybrid">Hybrid Router V0</option>
              </>
            )}
          </select>
        </div>

        {selectedRouter === 'hybrid' && (
          <HybridConfigPanel routers={routers} config={hybridConfig} onChange={onHybridConfigChange} />
        )}

        <QuickTestScenarios onSelect={handleScenarioSelect} />

        <div>
          <label className="block text-sm font-semibold mb-2 text-gray-700">Question</label>
          <input 
            type="text" 
            className="w-full border border-gray-300 rounded-md p-2.5 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 text-gray-800 shadow-sm" 
            placeholder="e.g. Giải giúp em phương trình x^2 = 4"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
          />
        </div>

        <div>
          <label className="block text-sm font-semibold mb-2 text-gray-700">Chat History (Optional)</label>
          <textarea 
            className="w-full border border-gray-300 rounded-md p-2.5 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 h-32 text-gray-800 shadow-sm text-sm" 
            placeholder="Student: Chào gia sư&#10;Tutor: Chào em, em cần hỗ trợ gì?"
            value={history}
            onChange={(e) => setHistory(e.target.value)}
          />
          <p className="text-xs text-gray-500 mt-1">One turn per line.</p>
        </div>

        <button 
          onClick={handleRun}
          disabled={loading}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 rounded-md shadow-sm transition-colors disabled:opacity-50"
        >
          {loading ? 'Routing...' : 'Run Router'}
        </button>
      </div>

      <div className="w-full md:w-1/2 pt-2 md:pt-0">
        {result || error ? (
           <RouterResultCard 
             title={`Result: ${currentRouterName}`}
             decision={result?.decision || null} 
             runtime={result?.runtime || null} 
             error={error} 
           />
        ) : (
           <div className="border-2 border-dashed border-gray-200 rounded-lg h-full min-h-[400px] flex flex-col items-center justify-center text-gray-400 bg-gray-50">
              <svg className="w-12 h-12 mb-3 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"></path></svg>
              <p>Run a router to see detailed results here</p>
           </div>
        )}
      </div>
    </div>
  );
}
