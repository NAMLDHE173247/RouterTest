"use client";

import { HybridConfig, RouterInfo } from '@/types/router';

interface Props {
  routers: RouterInfo[];
  config: HybridConfig;
  onChange: (config: HybridConfig) => void;
}

export default function HybridConfigPanel({ routers, config, onChange }: Props) {
  const ruleRouters = routers.filter((router) => router.family === 'rule_based' || router.id.startsWith('rule_'));
  const fallbackRouters = routers.filter((router) => router.capabilities?.can_be_hybrid_fallback === true);
  const availableFallbackCount = fallbackRouters.filter((router) => router.available !== false && router.status !== 'unavailable').length;

  const update = (patch: Partial<HybridConfig>) => onChange({ ...config, ...patch });

  return (
    <section className="bg-blue-50 border border-blue-200 rounded-lg p-4 space-y-4">
      <div>
        <h3 className="font-bold text-blue-900">Hybrid Router V0 Configuration</h3>
        <p className="text-xs text-blue-800 mt-1">Rule chạy trước; fallback Router chỉ được gọi khi policy kích hoạt.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <label className="text-sm font-semibold text-gray-700">
          Rule Router
          <select value={config.rule_router_id} onChange={(event) => update({ rule_router_id: event.target.value })} className="mt-1 w-full border rounded p-2 bg-white font-normal">
            {ruleRouters.map((router) => <option key={router.id} value={router.id}>{router.name}</option>)}
          </select>
        </label>
        <label className="text-sm font-semibold text-gray-700">
          Fallback Router
          <select value={config.fallback_router_id ?? ''} onChange={(event) => update({ fallback_router_id: event.target.value })} className="mt-1 w-full border rounded p-2 bg-white font-normal" disabled={fallbackRouters.length === 0}>
            <option value="" disabled>Chọn fallback Router</option>
            {fallbackRouters.map((router) => {
              const unavailable = router.available === false || router.status === 'unavailable';
              const source = router.family === 'slm' ? 'GPU' : 'OpenRouter';
              return <option key={router.id} value={router.id} disabled={unavailable}>{router.name} [{source}]{unavailable ? ` (${router.unavailable_reason ?? 'unavailable'})` : ''}</option>;
            })}
          </select>
          {availableFallbackCount === 0 && <span className="block mt-1 text-xs text-amber-700">Không có fallback Router đang available.</span>}
        </label>
      </div>

      <label className="block text-sm font-semibold text-gray-700">
        Rule confidence threshold: {config.rule_confidence_threshold.toFixed(2)}
        <input type="range" min="0" max="1" step="0.05" value={config.rule_confidence_threshold} onChange={(event) => update({ rule_confidence_threshold: Number(event.target.value) })} className="w-full" />
      </label>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-sm text-gray-700">
        <label><input type="checkbox" checked={config.fallback_on_low_confidence} onChange={(event) => update({ fallback_on_low_confidence: event.target.checked })} className="mr-2" />Fallback khi confidence thấp</label>
        <label><input type="checkbox" checked={config.fallback_on_unknown_subject} onChange={(event) => update({ fallback_on_unknown_subject: event.target.checked })} className="mr-2" />Fallback khi subject unknown</label>
        <label><input type="checkbox" checked={config.fallback_on_need_clarification} onChange={(event) => update({ fallback_on_need_clarification: event.target.checked })} className="mr-2" />Fallback khi cần clarification</label>
        <label><input type="checkbox" checked={config.fallback_on_rule_error} onChange={(event) => update({ fallback_on_rule_error: event.target.checked })} className="mr-2" />Fallback khi Rule lỗi</label>
      </div>

      <p className="text-xs text-gray-600">Fallback failure policy của V0: dùng lại Rule prediction nếu Rule đã tạo decision hợp lệ.</p>
    </section>
  );
}
