"use client";

import { useState } from 'react';
import { QUICK_TEST_SCENARIOS, QUICK_TEST_SCENARIO_GROUPS } from '@/lib/quickTestScenarios';
import { QuickTestScenario } from '@/types/router';

interface Props {
  onSelect: (scenario: QuickTestScenario) => void;
}

function formatExpectedRoute(scenario: QuickTestScenario): string {
  const { expectedRoute } = scenario;
  const secondary = expectedRoute.secondarySubjects.length > 0 ? ` + ${expectedRoute.secondarySubjects.join(', ')}` : '';
  return `${expectedRoute.primarySubject}${secondary} · ${expectedRoute.intent} · ${expectedRoute.targetSlm} · clarification: ${expectedRoute.needClarification ? 'Yes' : 'No'}`;
}

export default function QuickTestScenarios({ onSelect }: Props) {
  const [selectedScenario, setSelectedScenario] = useState<QuickTestScenario | null>(null);
  const [isOpen, setIsOpen] = useState(false);

  const handleSelect = (scenario: QuickTestScenario) => {
    setSelectedScenario(scenario);
    onSelect(scenario);
    setIsOpen(false);
  };

  return (
    <section className="relative" aria-labelledby="quick-test-scenarios-title">
      <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
        <div className="flex items-center justify-between gap-3">
          <div>
            <h3 id="quick-test-scenarios-title" className="font-bold text-slate-900">Quick Test Scenarios</h3>
            <p className="mt-1 text-xs text-slate-600">Chọn một mẫu để tự động điền question và history. Không phát sinh request API.</p>
          </div>
          <button
            type="button"
            aria-expanded={isOpen}
            aria-controls="quick-test-scenarios-popup"
            onClick={() => setIsOpen((open) => !open)}
            className="shrink-0 rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white transition-colors hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {isOpen ? 'Đóng' : 'Chọn mẫu'}
          </button>
        </div>
      </div>

      {isOpen && (
        <div id="quick-test-scenarios-popup" className="absolute inset-x-0 top-full z-20 mt-2 max-h-[min(70vh,520px)] overflow-y-auto rounded-lg border border-slate-200 bg-white p-4 shadow-xl" role="dialog" aria-label="Quick Test Scenarios">
          <div className="space-y-4">
            {QUICK_TEST_SCENARIO_GROUPS.map((group) => (
              <div key={group.id}>
                <h4 className="text-sm font-semibold text-slate-800">{group.title}</h4>
                <p className="mb-2 text-xs text-slate-500">{group.description}</p>
                <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
                  {QUICK_TEST_SCENARIOS.filter((scenario) => scenario.group === group.id).map((scenario) => (
                    <button
                      key={scenario.id}
                      type="button"
                      onClick={() => handleSelect(scenario)}
                      className="rounded-md border border-slate-300 bg-white p-3 text-left transition-colors hover:border-blue-400 hover:bg-blue-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <span className="block text-sm font-semibold text-slate-900">{scenario.title}</span>
                      <span className="mt-1 block text-xs text-slate-500">{scenario.note}</span>
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {selectedScenario && (
        <div className="mt-3 rounded-md border border-blue-200 bg-blue-50 p-3 text-xs text-blue-950" role="status">
          <p className="font-semibold">Selected: {selectedScenario.title}</p>
          <p className="mt-1"><span className="font-semibold">Expected labels:</span> {formatExpectedRoute(selectedScenario)}</p>
          <p className="mt-1"><span className="font-semibold">Expected with current Hybrid config:</span> {selectedScenario.expectedHybridBehavior}</p>
        </div>
      )}
    </section>
  );
}

export { formatExpectedRoute };
