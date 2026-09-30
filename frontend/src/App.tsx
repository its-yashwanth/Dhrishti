import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/layout/Layout';
import { DashboardPage } from './pages/DashboardPage';
import { EventAnalysisPage } from './pages/EventAnalysisPage';
import { ImpactCascadePage } from './pages/ImpactCascadePage';
import { SupplyChainPage } from './pages/SupplyChainPage';
import { VulnerabilityPage } from './pages/VulnerabilityPage';
import { StakeholderImpactPage } from './pages/StakeholderImpactPage';
import { MitigationPage } from './pages/MitigationPage';
import { EvidencePage } from './pages/EvidencePage';
import { ReportPage } from './pages/ReportPage';
import { ArchitecturePage } from './pages/ArchitecturePage';

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<DashboardPage />} />
          <Route path="event-analysis" element={<EventAnalysisPage />} />
          <Route path="cascade" element={<ImpactCascadePage />} />
          <Route path="supply-chain" element={<SupplyChainPage />} />
          <Route path="vulnerability" element={<VulnerabilityPage />} />
          <Route path="stakeholders" element={<StakeholderImpactPage />} />
          <Route path="mitigation" element={<MitigationPage />} />
          <Route path="evidence" element={<EvidencePage />} />
          <Route path="report" element={<ReportPage />} />
          <Route path="architecture" element={<ArchitecturePage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
