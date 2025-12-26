/**
 * Network Scan page component.
 *
 * Provides the interface for:
 * - Selecting a network target to scan
 * - Configuring scan options
 * - Viewing scan progress
 * - Reviewing scan results
 */

import { useState, useCallback, useEffect } from 'react';
import { Card, Button, Spinner, EmptyState, ErrorMessage, Progress, Badge } from '@/components/common';
import { useScan, useNetworkDetect, useNetworkValidation, useScanHistory } from '@/hooks';
import { useMode } from '@/context/ModeContext';
import type { ScanType, ScanRequest } from '@/types';
import { logger } from '@/services';
import styles from './NetworkScan.module.css';

const log = logger.create('NetworkScan');

/**
 * Scan type options with descriptions.
 */
const SCAN_TYPES: Array<{
  value: ScanType;
  label: string;
  description: string;
}> = [
  {
    value: 'quick',
    label: 'Quick Scan',
    description: 'Fast scan of common ports (22, 80, 443, etc.)',
  },
  {
    value: 'deep',
    label: 'Deep Scan',
    description: 'Comprehensive scan of all ports with service detection',
  },
  {
    value: 'vulnerability',
    label: 'Vulnerability Scan',
    description: 'Deep scan with vulnerability detection and analysis',
  },
];

/**
 * Network Scan page.
 */
export function NetworkScan() {
  // Form state
  const [target, setTarget] = useState('');
  const [scanType, setScanType] = useState<ScanType>('quick');
  const [userConsent, setUserConsent] = useState(false);

  // Hooks
  const { mode } = useMode();
  const { network: detectedNetwork, isLoading: detectingNetwork } = useNetworkDetect();
  const { validate, validation, isValidating, error: validationError, reset: resetValidation } =
    useNetworkValidation();
  const {
    scan,
    status,
    isScanning,
    progress,
    error: scanError,
    startScan,
    cancelScan,
    reset: resetScan,
  } = useScan();
  const { data: scanHistory, isLoading: historyLoading, refetch: refetchHistory } =
    useScanHistory({ page_size: 10 });

  // Load default scan type from localStorage on mount
  useEffect(() => {
    const savedScanType = localStorage.getItem('cybersec-default-scan-type');
    if (savedScanType && (savedScanType === 'quick' || savedScanType === 'deep' || savedScanType === 'discovery')) {
      setScanType(savedScanType as ScanType);
      log.info('Loaded default scan type from settings', { scanType: savedScanType });
    }
  }, []);

  // Auto-populate target from detected network (if setting is enabled)
  useEffect(() => {
    const autoDetectEnabled = localStorage.getItem('cybersec-auto-detect-network');
    const isEnabled = autoDetectEnabled === null || autoDetectEnabled === 'true';

    if (isEnabled && detectedNetwork?.network && !target) {
      // Convert detected network to /24 to avoid scanning too many hosts
      let networkToUse = detectedNetwork.network;
      if (networkToUse.includes('/')) {
        const [baseIp] = networkToUse.split('/');
        // Extract first three octets and use /24
        const octets = baseIp.split('.');
        if (octets.length >= 3) {
          networkToUse = `${octets[0]}.${octets[1]}.${octets[2]}.0/24`;
        }
      }
      setTarget(networkToUse);
      log.info('Auto-detected network', {
        original: detectedNetwork.network,
        adjusted: networkToUse
      });
    }
  }, [detectedNetwork, target]);

  /**
   * Handle target input change with debounced validation.
   */
  const handleTargetChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const value = e.target.value;
      setTarget(value);
      resetValidation();
    },
    [resetValidation]
  );

  /**
   * Validate the target when user stops typing.
   */
  const handleTargetBlur = useCallback(() => {
    if (target.trim()) {
      validate(target);
    }
  }, [target, validate]);

  /**
   * Handle form submission.
   */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!userConsent) {
      return;
    }

    // Validate target first
    if (!validation?.valid) {
      const result = await validate(target);
      if (!result?.valid) {
        return;
      }
    }

    const request: ScanRequest = {
      target,
      scan_type: scanType,
      user_consent: userConsent,
    };

    log.info('Starting scan', request);
    await startScan(request);
    refetchHistory();
  };

  /**
   * Handle new scan button.
   */
  const handleNewScan = () => {
    resetScan();
    setUserConsent(false);
  };

  /**
   * Format scan status for display.
   */
  const formatStatus = (statusValue: string): string => {
    return statusValue.charAt(0).toUpperCase() + statusValue.slice(1);
  };

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h1 className={styles.title}>Network Scan</h1>
        <p className={styles.subtitle}>
          Discover devices on your network and identify potential vulnerabilities
        </p>
      </header>

      <div className={styles.content}>
        {/* Scan Form / Progress */}
        <Card className={styles.scanCard}>
          {!isScanning && !scan ? (
            <form onSubmit={handleSubmit} className={styles.form}>
              {/* Target Input */}
              <div className={styles.formGroup}>
                <label htmlFor="target" className={styles.label}>
                  Network Target
                </label>
                <div className={styles.inputWrapper}>
                  <input
                    id="target"
                    type="text"
                    value={target}
                    onChange={handleTargetChange}
                    onBlur={handleTargetBlur}
                    placeholder="e.g., 192.168.1.0/24"
                    className={styles.input}
                    disabled={detectingNetwork}
                    aria-describedby="target-help target-validation"
                  />
                  {(detectingNetwork || isValidating) && (
                    <div className={styles.inputSpinner}>
                      <Spinner size="sm" label="Detecting network..." />
                    </div>
                  )}
                </div>
                <p id="target-help" className={styles.helpText}>
                  Enter an IP address or CIDR range (e.g., 192.168.1.0/24)
                </p>
                {validation && (
                  <div
                    id="target-validation"
                    className={`${styles.validation} ${validation.valid ? styles.valid : styles.invalid}`}
                    role="status"
                  >
                    {validation.valid ? (
                      <>
                        Valid {validation.type === 'network' ? 'network' : 'IP'} -{' '}
                        {validation.num_hosts} host{validation.num_hosts !== 1 ? 's' : ''}
                      </>
                    ) : (
                      validation.error || 'Invalid target'
                    )}
                  </div>
                )}
                {validationError && (
                  <p className={styles.errorText}>{validationError}</p>
                )}
              </div>

              {/* Scan Type Selection */}
              <fieldset className={styles.formGroup}>
                <legend className={styles.label}>Scan Type</legend>
                <div className={styles.scanTypeOptions}>
                  {SCAN_TYPES.map((type) => (
                    <label
                      key={type.value}
                      className={`${styles.scanTypeOption} ${scanType === type.value ? styles.selected : ''}`}
                    >
                      <input
                        type="radio"
                        name="scanType"
                        value={type.value}
                        checked={scanType === type.value}
                        onChange={() => setScanType(type.value)}
                        className={styles.radioInput}
                      />
                      <span className={styles.scanTypeLabel}>{type.label}</span>
                      <span className={styles.scanTypeDescription}>
                        {type.description}
                      </span>
                    </label>
                  ))}
                </div>
              </fieldset>

              {/* Mode-specific Information */}
              <div className={`${styles.modeInfo} ${mode === 'training' ? styles.modeInfoTraining : styles.modeInfoLive}`}>
                <div className={styles.modeInfoHeader}>
                  <span className={styles.modeInfoIcon} aria-hidden="true">
                    {mode === 'training' ? '🎓' : '⚠️'}
                  </span>
                  <h3 className={styles.modeInfoTitle}>
                    {mode === 'training' ? 'Training Mode Active' : 'Live Scanning Mode'}
                  </h3>
                </div>
                <p className={styles.modeInfoText}>
                  {mode === 'training'
                    ? 'This scan will use simulated network data for safe practice. No real network scanning will occur.'
                    : 'This scan will use nmap to perform real network scanning on your actual network. Only proceed if you own the network or have explicit permission to scan it.'}
                </p>
              </div>

              {/* Consent Checkbox */}
              <div className={styles.consentSection}>
                <label className={styles.consentLabel}>
                  <input
                    type="checkbox"
                    checked={userConsent}
                    onChange={(e) => setUserConsent(e.target.checked)}
                    className={styles.checkbox}
                  />
                  <span className={styles.consentText}>
                    {mode === 'training'
                      ? 'I understand this is a training scan using simulated network data for educational purposes.'
                      : 'I confirm that I own or have explicit permission to scan this network. Unauthorized network scanning may be illegal in my jurisdiction.'}
                  </span>
                </label>
              </div>

              {/* Error Display */}
              {scanError && (
                <ErrorMessage
                  message={scanError}
                  variant="inline"
                />
              )}

              {/* Submit Button */}
              <Button
                type="submit"
                variant="primary"
                size="lg"
                fullWidth
                disabled={!userConsent || !target.trim() || isValidating}
                isLoading={isValidating}
              >
                Start Scan
              </Button>
            </form>
          ) : isScanning ? (
            /* Scan Progress */
            <div className={styles.progressSection}>
              {scanError ? (
                <>
                  <h2 className={styles.progressTitle}>Scan Failed</h2>
                  <ErrorMessage
                    message={scanError}
                    variant="inline"
                  />
                  <Button
                    variant="primary"
                    onClick={handleNewScan}
                    className={styles.retryButton}
                  >
                    Try Again
                  </Button>
                </>
              ) : (
                <>
                  <h2 className={styles.progressTitle}>Scanning Network...</h2>
                  <p className={styles.progressTarget}>{status?.scan_id}</p>

                  <Progress
                    value={progress}
                    showLabel
                    label="Scan progress"
                    size="lg"
                  />

                  <div className={styles.progressStats}>
                    <div className={styles.progressStat}>
                      <span className={styles.progressStatLabel}>Status</span>
                      <Badge variant="primary">{formatStatus(status?.status || 'running')}</Badge>
                    </div>
                    <div className={styles.progressStat}>
                      <span className={styles.progressStatLabel}>Devices Found</span>
                      <span className={styles.progressStatValue}>
                        {status?.device_count || 0}
                      </span>
                    </div>
                  </div>

                  <Button
                    variant="destructive"
                    onClick={cancelScan}
                    className={styles.cancelButton}
                  >
                    Cancel Scan
                  </Button>
                </>
              )}
            </div>
          ) : scan ? (
            /* Scan Results */
            <div className={styles.resultsSection}>
              {scan.error_message && (
                <ErrorMessage
                  message={scan.error_message}
                  variant="inline"
                />
              )}
              <div className={styles.resultsHeader}>
                <h2 className={styles.resultsTitle}>Scan Complete</h2>
                <Button variant="outline" onClick={handleNewScan}>
                  New Scan
                </Button>
              </div>

              <div className={styles.resultsSummary}>
                <div className={styles.resultsStat}>
                  <span className={styles.resultsStatLabel}>Target</span>
                  <span className={styles.resultsStatValue}>{scan.target_range}</span>
                </div>
                <div className={styles.resultsStat}>
                  <span className={styles.resultsStatLabel}>Devices Found</span>
                  <span className={styles.resultsStatValue}>{scan.device_count}</span>
                </div>
                <div className={styles.resultsStat}>
                  <span className={styles.resultsStatLabel}>Duration</span>
                  <span className={styles.resultsStatValue}>
                    {scan.completed_at && scan.started_at
                      ? `${Math.round((new Date(scan.completed_at).getTime() - new Date(scan.started_at).getTime()) / 1000)}s`
                      : '-'}
                  </span>
                </div>
              </div>

              {scan.devices.length > 0 ? (
                <div className={styles.deviceList}>
                  <h3 className={styles.deviceListTitle}>Discovered Devices</h3>
                  <ul className={styles.devices}>
                    {scan.devices.map((device) => (
                      <li key={device.ip} className={styles.deviceItem}>
                        <div className={styles.deviceInfo}>
                          <span className={styles.deviceIp}>{device.ip}</span>
                          <span className={styles.deviceHostname}>
                            {device.hostname || 'Unknown'}
                          </span>
                        </div>
                        <div className={styles.deviceMeta}>
                          <span className={styles.deviceType}>
                            {device.device_type || 'Unknown device'}
                          </span>
                          <span className={styles.devicePorts}>
                            {device.open_ports.length} port{device.open_ports.length !== 1 ? 's' : ''} open
                          </span>
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : (
                <EmptyState
                  title="No devices found"
                  description="The scan completed but no devices were discovered on the target network."
                />
              )}
            </div>
          ) : null}
        </Card>

        {/* Scan History */}
        <Card
          title="Scan History"
          subtitle="Your previous network scans"
          className={styles.historyCard}
        >
          {historyLoading ? (
            <div className={styles.historyLoading}>
              <Spinner label="Loading scan history..." />
            </div>
          ) : scanHistory?.items && scanHistory.items.length > 0 ? (
            <ul className={styles.historyList}>
              {scanHistory.items.map((historyScan) => (
                <li key={historyScan.scan_id} className={styles.historyItem}>
                  <div className={styles.historyInfo}>
                    <span className={styles.historyTarget}>
                      {historyScan.target_range}
                    </span>
                    <span className={styles.historyTime}>
                      {historyScan.started_at
                        ? new Date(historyScan.started_at).toLocaleString()
                        : '-'}
                    </span>
                  </div>
                  <div className={styles.historyMeta}>
                    <Badge
                      variant={
                        historyScan.status === 'completed'
                          ? 'success'
                          : historyScan.status === 'failed'
                          ? 'destructive'
                          : 'default'
                      }
                      size="sm"
                    >
                      {formatStatus(historyScan.status)}
                    </Badge>
                    <span className={styles.historyDevices}>
                      {historyScan.device_count} device{historyScan.device_count !== 1 ? 's' : ''}
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <EmptyState
              title="No scan history"
              description="Your previous scans will appear here"
            />
          )}
        </Card>
      </div>
    </div>
  );
}
