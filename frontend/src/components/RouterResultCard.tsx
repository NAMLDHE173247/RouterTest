import React from 'react';
import { RouterDecision, RouterRuntime, RouterError } from '@/types/router';

interface Props {
  title?: string;
  decision: RouterDecision | null;
  runtime: RouterRuntime | null;
  error?: RouterError | null | string;
  diffFields?: string[];
}

export default function RouterResultCard({ title = "Result", decision, runtime, error, diffFields = [] }: Props) {
  if (error) {
    const errorMsg = typeof error === 'string' ? error : error.message;
    return (
      <div className="border border-red-200 rounded p-4 bg-red-50 shadow-sm">
        <h3 className="font-bold text-red-800 border-b border-red-200 pb-2">{title} - Error</h3>
        <p className="mt-2 text-red-600 text-sm">{errorMsg}</p>
      </div>
    );
  }

  if (!decision) return null;
  
  return (
    <div className="border border-gray-200 rounded p-4 bg-white shadow-sm space-y-4">
      <h3 className="font-bold text-lg border-b pb-2">{title}</h3>
      
      <div className="grid grid-cols-2 gap-4 text-sm">
        <div className={`p-1 rounded ${diffFields.includes('primary_subject') ? 'bg-yellow-100 outline outline-1 outline-yellow-400' : ''}`}>
          <p className="text-gray-500 mb-1">Primary Subject</p>
          <span className="font-medium text-blue-700 bg-blue-50 px-2 py-1 rounded inline-block">{decision.primary_subject}</span>
        </div>
        
        <div className={`p-1 rounded ${diffFields.includes('intent') ? 'bg-yellow-100 outline outline-1 outline-yellow-400' : ''}`}>
          <p className="text-gray-500 mb-1">Intent</p>
          <span className="font-medium text-purple-700 bg-purple-50 px-2 py-1 rounded inline-block">{decision.intent}</span>
        </div>
        
        <div className={`p-1 rounded ${diffFields.includes('target_slm') ? 'bg-yellow-100 outline outline-1 outline-yellow-400' : ''}`}>
          <p className="text-gray-500 mb-1">Target SLM</p>
          <span className="font-medium text-green-700 bg-green-50 px-2 py-1 rounded inline-block">{decision.target_slm}</span>
        </div>
        
        <div className="p-1">
          <p className="text-gray-500 mb-1">Confidence</p>
          <span className="font-medium text-gray-800 bg-gray-100 px-2 py-1 rounded inline-block">{decision.confidence.toFixed(2)}</span>
        </div>
      </div>
      
      {decision.secondary_subjects && decision.secondary_subjects.length > 0 && (
        <div className="text-sm">
          <p className="text-gray-500 mb-1">Secondary Subjects</p>
          <div className="flex flex-wrap gap-2">
            {decision.secondary_subjects.map((sub, i) => (
              <span key={i} className="text-xs bg-gray-100 border text-gray-700 px-2 py-1 rounded">{sub}</span>
            ))}
          </div>
        </div>
      )}

      {decision.need_clarification && (
        <div className={`text-sm p-1 rounded inline-block ${diffFields.includes('need_clarification') ? 'bg-yellow-100 outline outline-1 outline-yellow-400' : ''}`}>
          <span className="bg-yellow-100 text-yellow-800 text-xs px-2 py-1 rounded font-bold border border-yellow-200">Needs Clarification</span>
        </div>
      )}
      
      <div className="text-sm bg-gray-50 p-3 rounded border border-gray-100">
        <p className="text-gray-500 font-semibold mb-1">Reason:</p>
        <p className="text-gray-800">{decision.reason}</p>
      </div>
      
      <div className="text-xs text-gray-500 flex flex-wrap gap-4 pt-3 border-t">
        {runtime && (
          <>
            <span className="flex items-center gap-1">⏱ {runtime.latency_ms}ms</span>
            {runtime.input_tokens !== undefined && runtime.input_tokens > 0 && <span className="flex items-center gap-1">📥 In: {runtime.input_tokens}</span>}
            {runtime.output_tokens !== undefined && runtime.output_tokens > 0 && <span className="flex items-center gap-1">📤 Out: {runtime.output_tokens}</span>}
            <span className="flex items-center gap-1">{runtime.parse_success ? '✅ Success' : '❌ Parse Failed'}</span>
            {runtime.total_tokens !== undefined && runtime.total_tokens > 0 && <span>Total: {runtime.total_tokens}</span>}
            {runtime.model && <span className="bg-gray-100 px-2 py-0.5 rounded">🤖 {runtime.model}</span>}
            {runtime.structured_output_mode && <span>JSON: {runtime.structured_output_mode}</span>}
            {runtime.retry_count !== undefined && runtime.retry_count > 0 && <span>Retries: {runtime.retry_count}</span>}
            {runtime.cost !== undefined && runtime.cost !== null && <span>Cost: {runtime.cost}</span>}
          </>
        )}
      </div>

      {runtime?.hybrid && (
        <div className="text-xs bg-blue-50 border border-blue-100 rounded p-3 space-y-1">
          <p><span className="font-semibold">Hybrid source:</span> {runtime.hybrid.selected_source}</p>
          <p><span className="font-semibold">Fallback Router:</span> {runtime.hybrid.fallback_router_id}{runtime.hybrid.fallback_family ? ` (${runtime.hybrid.fallback_family})` : ''}</p>
          <p><span className="font-semibold">Fallback triggers:</span> {runtime.hybrid.fallback_triggers.length ? runtime.hybrid.fallback_triggers.join(', ') : 'none'}</p>
          <p><span className="font-semibold">Fallback called:</span> {runtime.hybrid.fallback_called ? 'yes' : 'no'}</p>
          {runtime.hybrid.degraded_mode && <p className="text-amber-700 font-semibold">Degraded mode: Rule fallback after LLM failure</p>}
        </div>
      )}
    </div>
  );
}
