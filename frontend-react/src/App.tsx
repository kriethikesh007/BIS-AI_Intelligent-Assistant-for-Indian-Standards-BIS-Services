import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AppShell } from './components/layout/AppShell';
import HomePage from './pages/HomePage';
import AssistantPage from './pages/AssistantPage';
import FindStandardPage from './pages/FindStandardPage';
import SearchPage from './pages/SearchPage';
import CertificationPage from './pages/CertificationPage';
import HallmarkingPage from './pages/HallmarkingPage';
import LaboratoryPage from './pages/LaboratoryPage';
import ConsumerPage from './pages/ConsumerPage';
import AnalyticsPage from './pages/AnalyticsPage';
import AdminPage from './pages/AdminPage';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<AppShell />}>
          <Route index element={<HomePage />} />
          <Route path="assistant" element={<AssistantPage />} />
          <Route path="find-standard" element={<FindStandardPage />} />
          <Route path="search" element={<SearchPage />} />
          <Route path="certification" element={<CertificationPage />} />
          <Route path="hallmarking" element={<HallmarkingPage />} />
          <Route path="laboratories" element={<LaboratoryPage />} />
          <Route path="consumer" element={<ConsumerPage />} />
          <Route path="analytics" element={<AnalyticsPage />} />
          <Route path="admin" element={<AdminPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
