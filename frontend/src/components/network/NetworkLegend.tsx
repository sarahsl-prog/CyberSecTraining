/**
 * NetworkLegend component.
 *
 * Displays a legend explaining the meaning of node colors and shapes
 * in the network visualization.
 */

import styles from './NetworkLegend.module.css';

/**
 * Severity legend items.
 */
const SEVERITY_ITEMS = [
  { label: 'Critical', color: 'var(--color-severity-critical, #dc2626)', description: '5+ vulnerabilities' },
  { label: 'High', color: 'var(--color-severity-high, #ea580c)', description: '3-4 vulnerabilities' },
  { label: 'Medium', color: 'var(--color-severity-medium, #ca8a04)', description: '1-2 vulnerabilities' },
  { label: 'Safe', color: 'var(--color-primary, #2563eb)', description: 'No vulnerabilities' },
];

/**
 * Device type legend items.
 */
const DEVICE_TYPES = [
  { label: 'Router', shape: 'diamond' },
  { label: 'Switch', shape: 'hexagon' },
  { label: 'Server', shape: 'rectangle' },
  { label: 'Computer', shape: 'rounded-rectangle' },
  { label: 'Other', shape: 'circle' },
];

/**
 * NetworkLegend component for explaining graph symbols.
 *
 * @example
 * ```tsx
 * <NetworkLegend />
 * ```
 */
export function NetworkLegend() {
  return (
    <div className={styles.legend} role="region" aria-label="Graph legend">
      <details className={styles.details} open>
        <summary className={styles.summary}>Legend</summary>
        <div className={styles.content}>
          {/* Severity Colors */}
          <div className={styles.section}>
            <h4 className={styles.sectionTitle}>Vulnerability Status</h4>
            <ul className={styles.list}>
              {SEVERITY_ITEMS.map((item) => (
                <li key={item.label} className={styles.item}>
                  <span
                    className={styles.colorSwatch}
                    style={{ backgroundColor: item.color }}
                    aria-hidden="true"
                  />
                  <span className={styles.itemLabel}>{item.label}</span>
                  <span className={styles.itemDescription}>{item.description}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Device Types */}
          <div className={styles.section}>
            <h4 className={styles.sectionTitle}>Device Types</h4>
            <ul className={styles.list}>
              {DEVICE_TYPES.map((item) => (
                <li key={item.label} className={styles.item}>
                  <span
                    className={`${styles.shapeSwatch} ${styles[item.shape]}`}
                    aria-hidden="true"
                  />
                  <span className={styles.itemLabel}>{item.label}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Status Indicators */}
          <div className={styles.section}>
            <h4 className={styles.sectionTitle}>Status</h4>
            <ul className={styles.list}>
              <li className={styles.item}>
                <span className={styles.statusSwatch} aria-hidden="true" />
                <span className={styles.itemLabel}>Online</span>
              </li>
              <li className={styles.item}>
                <span
                  className={`${styles.statusSwatch} ${styles.offline}`}
                  aria-hidden="true"
                />
                <span className={styles.itemLabel}>Offline</span>
              </li>
            </ul>
          </div>
        </div>
      </details>
    </div>
  );
}
