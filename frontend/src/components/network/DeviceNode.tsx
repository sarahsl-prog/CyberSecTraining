/**
 * DeviceNode component.
 *
 * A standalone device node display component for use outside the graph,
 * such as in device lists or tooltips. Matches the visual style of
 * nodes in the network graph.
 */

import type { Device } from '@/types';
import { Badge } from '@/components/common';
import styles from './DeviceNode.module.css';

/**
 * Props for DeviceNode component.
 */
export interface DeviceNodeProps {
  /** Device to display */
  device: Device;
  /** Whether the node is selected */
  isSelected?: boolean;
  /** Click handler */
  onClick?: () => void;
  /** Size variant */
  size?: 'sm' | 'md' | 'lg';
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
  };
  return icons[deviceType || ''] || '📟';
}

/**
 * Get severity level for styling.
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
 * DeviceNode component for displaying a device with its status.
 *
 * @example
 * ```tsx
 * <DeviceNode
 *   device={device}
 *   isSelected={selectedId === device.id}
 *   onClick={() => selectDevice(device.id)}
 * />
 * ```
 */
export function DeviceNode({
  device,
  isSelected = false,
  onClick,
  size = 'md',
}: DeviceNodeProps) {
  const severity = getSeverityLevel(device.vulnerability_count);
  const icon = getDeviceIcon(device.device_type);

  return (
    <button
      type="button"
      className={`${styles.node} ${styles[`size-${size}`]} ${
        isSelected ? styles.selected : ''
      } ${!device.is_up ? styles.offline : ''} ${
        severity ? styles[`severity-${severity}`] : ''
      }`}
      onClick={onClick}
      aria-pressed={isSelected}
      aria-label={`${device.hostname || device.ip}, ${device.device_type || 'Unknown device'}, ${
        device.vulnerability_count
      } vulnerabilities, ${device.is_up ? 'online' : 'offline'}`}
    >
      <span className={styles.icon} aria-hidden="true">
        {icon}
      </span>
      <span className={styles.info}>
        <span className={styles.hostname}>{device.hostname || device.ip}</span>
        <span className={styles.ip}>{device.hostname ? device.ip : ''}</span>
      </span>
      {device.vulnerability_count > 0 && (
        <Badge severity={severity} size="sm" className={styles.badge}>
          {device.vulnerability_count}
        </Badge>
      )}
      {!device.is_up && (
        <span className={styles.offlineIndicator} aria-hidden="true">
          ●
        </span>
      )}
    </button>
  );
}
