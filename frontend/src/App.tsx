import { Routes, Route, Navigate } from 'react-router-dom';
import { MainLayout } from '@/components/layout/MainLayout';

// Page imports (to be implemented)
// import { Dashboard } from '@/pages/Dashboard';
// import { NetworkScan } from '@/pages/NetworkScan';
// import { Scenarios } from '@/pages/Scenarios';
// import { Settings } from '@/pages/Settings';

function App() {
  return (
    <Routes>
      <Route path="/" element={<MainLayout />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<PlaceholderPage title="Dashboard" />} />
        <Route path="scan" element={<PlaceholderPage title="Network Scan" />} />
        <Route path="scenarios" element={<PlaceholderPage title="Scenarios" />} />
        <Route path="community" element={<PlaceholderPage title="Community" />} />
        <Route path="settings" element={<PlaceholderPage title="Settings" />} />
      </Route>
    </Routes>
  );
}

// Temporary placeholder component
function PlaceholderPage({ title }: { title: string }) {
  return (
    <div style={{ padding: '2rem' }}>
      <h1>{title}</h1>
      <p>This page is under construction.</p>
    </div>
  );
}

export default App;
