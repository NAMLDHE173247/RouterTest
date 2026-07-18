"use client";

import React, { useState } from 'react';
import { compareRouters, getQwenServiceUrl } from '@/lib/api';
import { CompareResult, HybridConfig, RouterInfo, RouterDecision } from '@/types/router';
import RouterResultCard from './RouterResultCard';
import HybridConfigPanel from './HybridConfigPanel';

interface Props {
  routers: RouterInfo[];
  hybridConfig: HybridConfig;
  onHybridConfigChange: (config: HybridConfig) => void;
}

export default function RouterComparison({ routers, hybridConfig, onHybridConfigChange }: Props) {
  const [selectedRouterIds, setSelectedRouterIds] = useState<string[]>([]);
  const [question, setQuestion] = useState('');
  const [history, setHistory] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<CompareResult[]>([]);
  const [error, setError] = useState<string | null>(null);

  const toggleRouter = (id: string) => {
    setSelectedRouterIds(prev => 
      prev.includes(id) ? prev.filter(r => r !== id) : [...prev, id]
    );
  };

  const handleCompare = async () => {
    if (selectedRouterIds.length < 2) {
      setError('Vui lòng chọn ít nhất 2 Router để so sánh');
      return;
    }

    if (!question.trim()) {
      setError('Vui lòng nhập câu hỏi');
      return;
    }
    
    // Check Qwen config if selected
    if (selectedRouterIds.includes('qwen_v0')) {
       try {
         const config = await getQwenServiceUrl();
         if (!config.url) {
            setError('Qwen GPU Service URL is not configured. Please configure it in the settings tab.');
            return;
         }
       } catch (e) {
         // Proceed to let backend handle 500/503 partial failure gracefully
       }
    }

    setLoading(true);
    setError(null);
    setResults([]);

    const historyArray = history.split('\n').map(s => s.trim()).filter(s => s.length > 0);

    try {
      const res = await compareRouters({
        question: question,
        history: historyArray,
        router_ids: selectedRouterIds,
        hybrid_config: selectedRouterIds.includes('hybrid') ? hybridConfig : undefined,
      });
      setResults(res.comparisons || []);
    } catch (e: any) {
      setError(e.message || String(e));
    } finally {
      setLoading(false);
    }
  };

  // Compute diffs dynamically across ALL selected results
  const computeDiffs = (resultsList: CompareResult[]) => {
    const validDecisions = resultsList
      .filter(r => r.response?.decision)
      .map(r => r.response!.decision!);
    
    if (validDecisions.length < 2) return [];

    const diffFields: string[] = [];
    const fieldsToCheck = ['primary_subject', 'intent', 'target_slm', 'need_clarification'] as const;
    
    fieldsToCheck.forEach(field => {
      const uniqueValues = new Set(validDecisions.map(d => String(d[field])));
      if (uniqueValues.size > 1) {
        diffFields.push(field);
      }
    });

    // Handle secondary_subjects normalization and diff
    const normalizeSecondary = (arr?: string[]) => {
      if (!arr || arr.length === 0) return '';
      return [...arr].sort().join(',');
    };

    const uniqueSecondary = new Set(validDecisions.map(d => normalizeSecondary(d.secondary_subjects)));
    if (uniqueSecondary.size > 1) {
      diffFields.push('secondary_subjects');
    }

    return diffFields;
  };

  const diffFields = computeDiffs(results);

  // Use a fallback for routers if the API failed to fetch them
  const availableRouters = routers.length > 0 ? routers : [
    { id: 'rule_v0', name: 'Rule-based Router V0', status: 'ready', enabled: true },
    { id: 'rule_v1', name: 'Rule-based Router V1', status: 'ready', enabled: true },
    { id: 'rule_v2', name: 'Rule-based Router V2', status: 'ready', enabled: true },
    { id: 'rule_v3', name: 'Rule-based Router V3 (Phase 0)', status: 'ready', enabled: true },
    { id: 'qwen_v0', name: 'Qwen Router V0 (GPU Service)', status: 'ready', enabled: true },
    { id: 'llm_deepseek_v0', name: 'LLM Router DeepSeek V0', status: 'unavailable', enabled: true },
    { id: 'llm_gemini_v0', name: 'LLM Router Gemini V0', status: 'unavailable', enabled: true },
    { id: 'llm_openai_v0', name: 'LLM Router OpenAI V0', status: 'unavailable', enabled: true },
    { id: 'hybrid', name: 'Hybrid Router V0', status: 'ready', enabled: true }
  ];

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
        <h2 className="text-xl font-bold mb-4 text-gray-800">Router Comparison</h2>
        
        <div className="space-y-5">
          <div>
            <label className="block text-sm font-semibold mb-2 text-gray-700">Select Routers to Compare</label>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
              {availableRouters.map(r => {
                const isLLM = r.id.startsWith('llm_');
                const isDisabled = (!isLLM && r.status && r.status !== 'ready') || (r as any).enabled === false;
                return (
                  <label 
                    key={r.id} 
                    className={`flex items-start gap-2 p-3 rounded border cursor-pointer transition-colors ${isDisabled ? 'bg-gray-50 opacity-60 cursor-not-allowed' : selectedRouterIds.includes(r.id) ? 'bg-blue-50 border-blue-200' : 'bg-white hover:bg-gray-50'}`}
                  >
                    <input 
                      type="checkbox" 
                      className="mt-1 w-4 h-4 text-blue-600 focus:ring-blue-500 rounded border-gray-300 disabled:opacity-50"
                      checked={selectedRouterIds.includes(r.id)}
                      onChange={() => toggleRouter(r.id)}
                      disabled={isDisabled}
                    />
                    <div className="flex flex-col">
                      <span className="text-sm font-medium text-gray-800">
                        {r.name}
                      </span>
                      {r.id === 'hybrid' && <span className="text-xs text-amber-600 font-semibold">Coming soon</span>}
                    </div>
                  </label>
                );
              })}
            </div>
            {selectedRouterIds.length < 2 && (
              <p className="text-sm text-red-500 mt-2 font-medium">Please select at least 2 routers to compare.</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-semibold mb-1 text-gray-700">Question</label>
            <input 
              type="text" 
              className="w-full border border-gray-300 rounded p-2 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 text-gray-800" 
              placeholder="e.g. Tại sao trời lại mưa?"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
            />
          </div>

          {selectedRouterIds.includes('hybrid') && (
            <HybridConfigPanel routers={routers} config={hybridConfig} onChange={onHybridConfigChange} />
          )}

          <div>
            <label className="block text-sm font-semibold mb-1 text-gray-700">History (Optional)</label>
            <textarea 
              className="w-full border border-gray-300 rounded p-2 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 h-20 text-gray-800 text-sm" 
              placeholder="One turn per line."
              value={history}
              onChange={(e) => setHistory(e.target.value)}
            />
          </div>

          <button 
            onClick={handleCompare}
            disabled={loading || selectedRouterIds.length < 2}
            className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-2.5 px-6 rounded-md shadow-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Comparing...' : 'Compare Selected Routers'}
          </button>
          
          {error && <div className="text-red-600 text-sm mt-2">{error}</div>}
        </div>
      </div>

      {results.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          {results.map((res) => {
            const routerInfo = availableRouters.find(r => r.id === res.router_id);
            const title = routerInfo ? routerInfo.name : res.router_id;
            
            return (
              <RouterResultCard 
                key={res.router_id}
                title={title}
                decision={res.response?.decision || null}
                runtime={res.response?.runtime || null}
                error={res.error}
                diffFields={diffFields}
              />
            );
          })}
        </div>
      )}
    </div>
  );
}
