/**
 * Dashboard page component.
 *
 * The main dashboard provides an overview of network security status including:
 * - Network status summary
 * - Recent scan history
 * - Vulnerability summary by severity
 * - Quick action buttons
 */

import { useNavigate } from 'react-router-dom';
import { Card, Button, Spinner, EmptyState, ErrorMessage, Badge } from '@/components/common';
import { useScanHistory, useVulnerabilitySummary, useDeviceList } from '@/hooks';
import { logger } from '@/services';
import styles from './Dashboard.module.css';

const log = logger.create('Dashboard');

/**
 * Dashboard page.
 *
 * Provides a high-level overview of network security status
 * with quick access to common actions.
 */
export function Dashboard() {
  const navigate = useNavigate();

  // Fetch dashboard data
  const { data: scans, isLoading: scansLoading, error: scansError, refetch: refetchScans } =
    useScanHistory({ page_size: 5 });
  const { summary, isLoading: summaryLoading, error: summaryError, refetch: refetchSummary } =
    useVulnerabilitySummary();
  const { total: deviceCount, isLoading: devicesLoading } =
    useDeviceList({ page_size: 1 });

  log.debug('Dashboard rendering', {
    scansLoading,
    summaryLoading,
    devicesLoading,
  });

  /**
   * Navigate to scan page.
   */
  const handleStartScan = () => {
    navigate('/scan');
  };

  /**
   * Format relative time.
   */
  const formatRelativeTime = (dateString?: string): string => {
    if (!dateString) return 'Never';
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} min ago`;

    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;

    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
  };

  return (
    <div className={styles.dashboard}>
      <header className={styles.header}>
        <div>
          <h1 className={styles.title}>Dashboard</h1>
          <p className={styles.subtitle}>
            Network security overview and quick actions
          </p>
        </div>
        <Button variant="primary" onClick={handleStartScan} size="lg">
          Start New Scan
        </Button>
      </header>

      {/* Stats Cards */}
      <section className={styles.statsGrid} aria-label="Network statistics">
        <StatCard
          title="Total Devices"
          value={deviceCount}
          isLoading={devicesLoading}
          icon="devices"
        />
        <StatCard
          title="Vulnerabilities"
          value={summary?.unfixed ?? 0}
          isLoading={summaryLoading}
          icon="vulnerabilities"
          variant={summary?.unfixed && summary.unfixed > 0 ? 'warning' : 'default'}
        />
        <StatCard
          title="Critical Issues"
          value={summary?.critical ?? 0}
          isLoading={summaryLoading}
          icon="critical"
          variant={summary?.critical && summary.critical > 0 ? 'danger' : 'default'}
        />
        <StatCard
          title="Fixed"
          value={summary?.fixed ?? 0}
          isLoading={summaryLoading}
          icon="fixed"
          variant="success"
        />
      </section>

      <div className={styles.contentGrid}>
        {/* Vulnerability Summary */}
        <Card
          title="Vulnerability Summary"
          subtitle="Issues by severity level"
          className={styles.vulnSummary}
        >
          {summaryLoading ? (
            <div className={styles.loadingContainer}>
              <Spinner label="Loading vulnerability summary..." />
            </div>
          ) : summaryError ? (
            <ErrorMessage
              message={summaryError.detail}
              onRetry={refetchSummary}
            />
          ) : summary ? (
            <VulnerabilitySummaryChart summary={summary} />
          ) : (
            <EmptyState
              title="No data"
              description="Run a scan to detect vulnerabilities"
            />
          )}
        </Card>

        {/* Recent Scans */}
        <Card
          title="Recent Scans"
          subtitle="Your latest network scans"
          action={
            scans?.items && scans.items.length > 0 ? (
              <Button variant="ghost" size="sm" onClick={() => navigate('/scan')}>
                View all
              </Button>
            ) : null
          }
          className={styles.recentScans}
        >
          {scansLoading ? (
            <div className={styles.loadingContainer}>
              <Spinner label="Loading recent scans..." />
            </div>
          ) : scansError ? (
            <ErrorMessage message={scansError.detail} onRetry={refetchScans} />
          ) : scans?.items && scans.items.length > 0 ? (
            <ul className={styles.scanList}>
              {scans.items.map((scan) => (
                <li key={scan.scan_id} className={styles.scanItem}>
                  <div className={styles.scanInfo}>
                    <span className={styles.scanTarget}>{scan.target_range}</span>
                    <span className={styles.scanTime}>
                      {formatRelativeTime(scan.completed_at || scan.started_at)}
                    </span>
                  </div>
                  <div className={styles.scanMeta}>
                    <Badge
                      variant={scan.status === 'completed' ? 'success' : 'default'}
                      size="sm"
                    >
                      {scan.status}
                    </Badge>
                    <span className={styles.deviceCount}>
                      {scan.device_count} device{scan.device_count !== 1 ? 's' : ''}
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <EmptyState
              title="No scans yet"
              description="Start your first network scan to discover devices"
              action={
                <Button variant="primary" onClick={handleStartScan}>
                  Start Scan
                </Button>
              }
            />
          )}
        </Card>

        {/* Quick Actions */}
        <Card title="Quick Actions" className={styles.quickActions}>
          <div className={styles.actionButtons}>
            <Button
              variant="outline"
              fullWidth
              onClick={() => navigate('/scan')}
              leftIcon={<ScanIcon />}
            >
              Network Scan
            </Button>
            <Button
              variant="outline"
              fullWidth
              onClick={() => navigate('/scenarios')}
              leftIcon={<ScenariosIcon />}
            >
              View Scenarios
            </Button>
            <Button
              variant="outline"
              fullWidth
              onClick={() => navigate('/settings')}
              leftIcon={<SettingsIcon />}
            >
              Settings
            </Button>
          </div>
        </Card>
      </div>
    </div>
  );
}

/**
 * Stats card component for dashboard metrics.
 */
interface StatCardProps {
  title: string;
  value: number;
  isLoading?: boolean;
  icon?: string;
  variant?: 'default' | 'warning' | 'danger' | 'success';
}

function StatCard({ title, value, isLoading, icon, variant = 'default' }: StatCardProps) {
  return (
    <div className={`${styles.statCard} ${styles[`stat-${variant}`]}`}>
      <div className={styles.statIcon} aria-hidden="true">
        {icon === 'devices' && <DevicesIcon />}
        {icon === 'vulnerabilities' && <VulnIcon />}
        {icon === 'critical' && <CriticalIcon />}
        {icon === 'fixed' && <FixedIcon />}
      </div>
      <div className={styles.statContent}>
        <span className={styles.statTitle}>{title}</span>
        {isLoading ? (
          <Spinner size="sm" />
        ) : (
          <span className={styles.statValue}>{value}</span>
        )}
      </div>
    </div>
  );
}

/**
 * Vulnerability summary chart component.
 */
interface VulnerabilitySummaryChartProps {
  summary: {
    critical: number;
    high: number;
    medium: number;
    low: number;
    info: number;
    total: number;
  };
}

function VulnerabilitySummaryChart({ summary }: VulnerabilitySummaryChartProps) {
  const severities = [
    { key: 'critical', label: 'Critical', count: summary.critical },
    { key: 'high', label: 'High', count: summary.high },
    { key: 'medium', label: 'Medium', count: summary.medium },
    { key: 'low', label: 'Low', count: summary.low },
    { key: 'info', label: 'Info', count: summary.info },
  ];

  const maxCount = Math.max(...severities.map((s) => s.count), 1);

  return (
    <div className={styles.severityChart}>
      {severities.map((sev) => (
        <div key={sev.key} className={styles.severityRow}>
          <span className={styles.severityLabel}>{sev.label}</span>
          <div className={styles.severityBar}>
            <div
              className={`${styles.severityFill} ${styles[`severity-${sev.key}`]}`}
              style={{ width: `${(sev.count / maxCount) * 100}%` }}
              role="progressbar"
              aria-valuenow={sev.count}
              aria-valuemax={maxCount}
              aria-label={`${sev.label}: ${sev.count}`}
            />
          </div>
          <span className={styles.severityCount}>{sev.count}</span>
        </div>
      ))}
    </div>
  );
}

// Simple icon components
function DevicesIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <rect x="4" y="4" width="16" height="12" rx="2" />
      <path d="M8 20h8M12 16v4" />
    </svg>
  );
}

function VulnIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
    </svg>
  );
}

function CriticalIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="12" r="10" />
      <path d="M12 8v4m0 4h.01" />
    </svg>
  );
}

function FixedIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  );
}

function ScanIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="20" height="20">
      <circle cx="11" cy="11" r="8" />
      <path d="M21 21l-4.35-4.35" />
    </svg>
  );
}

function ScenariosIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="20" height="20">
      <path d="M4 19.5A2.5 2.5 0 016.5 17H20" />
      <path d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z" />
    </svg>
  );
}

function SettingsIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="20" height="20">
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2 2 2 0 01-2-2v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 01-2-2 2 2 0 012-2h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06a1.65 1.65 0 001.82.33H9a1.65 1.65 0 001-1.51V3a2 2 0 012-2 2 2 0 012 2v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 012 2 2 2 0 01-2 2h-.09a1.65 1.65 0 00-1.51 1z" />
    </svg>
  );
}
