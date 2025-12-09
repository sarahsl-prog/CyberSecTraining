/**
 * DeviceDetail component.
 *
 * Displays detailed information about a selected device in a modal dialog.
 * Shows device properties, open ports, and vulnerability summary with
 * links to view detailed vulnerability information.
 */

import type { Device, Vulnerability } from '@/types';
import { Modal, Badge, Button, Spinner, ErrorMessage } from '@/components/common';
import { useVulnerabilities } from '@/hooks';
import { logger } from '@/services/logger';
import styles from './DeviceDetail.module.css';

/**
 * Props for DeviceDetail component.
 */
export interface DeviceDetailProps {
  /** Device to display details for */
  device: Device | null;
  /** Whether the modal is open */
  isOpen: boolean;
  /** Handler called when modal should close */
  onClose: () => void;
  /** Handler called when a vulnerability is selected */
  onVulnerabilitySelect?: (vulnerability: Vulnerability) => void;
}

/**
 * Get device icon based on type.
 */
function getDeviceIcon(deviceType?: string): string {
  const icons: Record<string, string> = {
    router: '🌐',
    switch: '🔀',
    server: '🖥️',
    computer: '💻',
    laptop: '💻',
    phone: '📱',
    tablet: '📱',
    printer: '🖨️',
    camera: '📷',
    iot: '📡',
    storage: '💾',
    access_point: '📶',
  };
  return icons[deviceType || ''] || '📟';
}

/**
 * Format timestamp for display.
 */
function formatTimestamp(isoString?: string): string {
  if (!isoString) return 'Unknown';
  try {
    const date = new Date(isoString);
    return date.toLocaleString();
  } catch {
    return 'Unknown';
  }
}

/**
 * Get severity level for display.
 */
function getSeverityLevel(
  vulnCount: number
): 'critical' | 'high' | 'medium' | 'low' | undefined {
  if (vulnCount >= 5) return 'critical';
  if (vulnCount >= 3) return 'high';
  if (vulnCount >= 1) return 'medium';
  return undefined;
}

/**
 * DeviceDetail component for showing device information.
 *
 * @example
 * ```tsx
 * <DeviceDetail
 *   device={selectedDevice}
 *   isOpen={showDeviceDetail}
 *   onClose={() => setShowDeviceDetail(false)}
 *   onVulnerabilitySelect={(vuln) => setSelectedVuln(vuln)}
 * />
 * ```
 */
export function DeviceDetail({
  device,
  isOpen,
  onClose,
  onVulnerabilitySelect,
}: DeviceDetailProps) {
  // Fetch vulnerabilities for this device
  const {
    data: vulnerabilities,
    loading,
    error,
  } = useVulnerabilities(device?.id ? { device_id: device.id } : undefined);

  // Log when device detail is opened
  if (isOpen && device) {
    logger.debug('DeviceDetail opened', { deviceId: device.id, ip: device.ip });
  }

  if (!device) {
    return null;
  }

  const severity = getSeverityLevel(device.vulnerability_count);
  const icon = getDeviceIcon(device.device_type);

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Device Details"
      size="lg"
      aria-describedby="device-description"
    >
      <div className={styles.detail}>
        {/* Device Header */}
        <header className={styles.header}>
          <span className={styles.icon} aria-hidden="true">
            {icon}
          </span>
          <div className={styles.headerInfo}>
            <h3 className={styles.hostname}>
              {device.hostname || device.ip}
            </h3>
            <span className={styles.deviceType}>
              {device.device_type || 'Unknown device'}
            </span>
          </div>
          <div className={styles.statusBadges}>
            <Badge
              severity={device.is_up ? undefined : 'medium'}
              size="sm"
            >
              {device.is_up ? 'Online' : 'Offline'}
            </Badge>
            {severity && (
              <Badge severity={severity} size="sm">
                {device.vulnerability_count} vulnerabilities
              </Badge>
            )}
          </div>
        </header>

        {/* Device Properties */}
        <section className={styles.section} aria-labelledby="device-props-heading">
          <h4 id="device-props-heading" className={styles.sectionTitle}>
            Device Information
          </h4>
          <dl className={styles.propertyList} id="device-description">
            <div className={styles.property}>
              <dt>IP Address</dt>
              <dd className={styles.monospace}>{device.ip}</dd>
            </div>
            {device.mac && (
              <div className={styles.property}>
                <dt>MAC Address</dt>
                <dd className={styles.monospace}>{device.mac}</dd>
              </div>
            )}
            {device.vendor && (
              <div className={styles.property}>
                <dt>Manufacturer</dt>
                <dd>{device.vendor}</dd>
              </div>
            )}
            {device.os && (
              <div className={styles.property}>
                <dt>Operating System</dt>
                <dd>
                  {device.os}
                  {device.os_accuracy > 0 && (
                    <span className={styles.confidence}>
                      {' '}({device.os_accuracy}% confidence)
                    </span>
                  )}
                </dd>
              </div>
            )}
            {device.last_seen && (
              <div className={styles.property}>
                <dt>Last Seen</dt>
                <dd>{formatTimestamp(device.last_seen)}</dd>
              </div>
            )}
          </dl>
        </section>

        {/* Open Ports */}
        {device.open_ports && device.open_ports.length > 0 && (
          <section className={styles.section} aria-labelledby="ports-heading">
            <h4 id="ports-heading" className={styles.sectionTitle}>
              Open Ports ({device.open_ports.length})
            </h4>
            <div className={styles.portsGrid}>
              {device.open_ports.map((port) => (
                <div key={port.port} className={styles.portItem}>
                  <span className={styles.portNumber}>{port.port}</span>
                  <span className={styles.portProtocol}>/{port.protocol}</span>
                  {port.service && (
                    <span className={styles.portService}>{port.service}</span>
                  )}
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Vulnerabilities */}
        <section className={styles.section} aria-labelledby="vulns-heading">
          <h4 id="vulns-heading" className={styles.sectionTitle}>
            Vulnerabilities
          </h4>
          {loading ? (
            <div className={styles.loadingState}>
              <Spinner size="sm" />
              <span>Loading vulnerabilities...</span>
            </div>
          ) : error ? (
            <ErrorMessage
              title="Failed to load vulnerabilities"
              message={error}
              compact
            />
          ) : vulnerabilities && vulnerabilities.length > 0 ? (
            <ul className={styles.vulnList}>
              {vulnerabilities.map((vuln) => (
                <li key={vuln.id}>
                  <button
                    type="button"
                    className={styles.vulnItem}
                    onClick={() => onVulnerabilitySelect?.(vuln)}
                    aria-label={`${vuln.title || vuln.vuln_type}, ${vuln.severity} severity. Click for details.`}
                  >
                    <Badge severity={vuln.severity} size="sm">
                      {vuln.severity}
                    </Badge>
                    <span className={styles.vulnTitle}>
                      {vuln.title || vuln.vuln_type}
                    </span>
                    {vuln.is_fixed && (
                      <Badge severity="low" size="sm">
                        Fixed
                      </Badge>
                    )}
                    <span className={styles.vulnArrow} aria-hidden="true">
                      →
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          ) : (
            <p className={styles.noVulns}>
              No vulnerabilities detected on this device.
            </p>
          )}
        </section>

        {/* Actions */}
        <footer className={styles.footer}>
          <Button variant="secondary" onClick={onClose}>
            Close
          </Button>
        </footer>
      </div>
    </Modal>
  );
}
