import { Routes, Route, Navigate } from 'react-router-dom';
import { MainLayout } from '@/components/layout/MainLayout';
import { Dashboard } from '@/pages/Dashboard';
import { NetworkScan } from '@/pages/NetworkScan';
import { Scenarios } from '@/pages/Scenarios';
import { Settings } from '@/pages/Settings';

/**
 * Main application component.
 *
 * Defines the application routes using React Router.
 * All pages are rendered within the MainLayout which provides
 * consistent header, sidebar, and accessibility features.
 */
function App() {
  return (
    <Routes>
      <Route path="/" element={<MainLayout />}>
        {/* Redirect root to dashboard */}
        <Route index element={<Navigate to="/dashboard" replace />} />

        {/* Main pages */}
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="scan" element={<NetworkScan />} />
        <Route path="scenarios" element={<Scenarios />} />
        <Route path="scenarios/:scenarioId" element={<PlaceholderPage title="Scenario Details" />} />
        <Route path="scenarios/:scenarioId/play" element={<PlaceholderPage title="Scenario Player" />} />
        <Route path="settings" element={<Settings />} />

        {/* Placeholder pages for future implementation */}
        <Route path="community" element={<PlaceholderPage title="Community" />} />
      </Route>
    </Routes>
  );
}

/**
 * Placeholder component for pages not yet implemented.
 */
function PlaceholderPage({ title }: { title: string }) {
  return (
    <div style={{ padding: '2rem' }}>
      <h1>{title}</h1>
      <p style={{ color: 'var(--color-muted-foreground)' }}>
        This feature is coming soon. Check back later!
      </p>
    </div>
  );
}

export default App;
