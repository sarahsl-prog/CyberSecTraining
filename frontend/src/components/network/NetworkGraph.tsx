/**
 * NetworkGraph component.
 *
 * Interactive network topology visualization using Cytoscape.js.
 * Displays devices as nodes with connections and vulnerability indicators.
 *
 * Features:
 * - Device nodes with severity-based coloring
 * - Zoom/pan controls
 * - Keyboard navigation for accessibility
 * - Click handlers for device selection
 * - Responsive layout
 */

import { useEffect, useRef, useCallback, useState } from 'react';
import cytoscape, { Core, NodeSingular, EventObject } from 'cytoscape';
import type { Device } from '@/types';
import { logger } from '@/services';
import { NetworkControls } from './NetworkControls';
import { NetworkLegend } from './NetworkLegend';
import styles from './NetworkGraph.module.css';

const log = logger.create('NetworkGraph');

/**
 * Props for NetworkGraph component.
 */
export interface NetworkGraphProps {
  /** Devices to display in the graph */
  devices: Device[];
  /** Currently selected device ID */
  selectedDeviceId?: string | null;
  /** Callback when a device is selected */
  onDeviceSelect?: (device: Device | null) => void;
  /** Callback when a device is double-clicked */
  onDeviceDoubleClick?: (device: Device) => void;
  /** Gateway/router IP for central node */
  gatewayIp?: string;
  /** Whether to show the legend */
  showLegend?: boolean;
  /** Whether to show controls */
  showControls?: boolean;
  /** Accessible label for the graph */
  ariaLabel?: string;
}

/**
 * Get severity level for a device based on vulnerability count.
 */
function getDeviceSeverity(device: Device): 'critical' | 'high' | 'medium' | 'low' | 'none' {
  if (device.vulnerability_count >= 5) return 'critical';
  if (device.vulnerability_count >= 3) return 'high';
  if (device.vulnerability_count >= 1) return 'medium';
  return 'none';
}

/**
 * Get node color based on severity.
 */
function getSeverityColor(severity: string): string {
  const colors: Record<string, string> = {
    critical: 'var(--color-severity-critical, #dc2626)',
    high: 'var(--color-severity-high, #ea580c)',
    medium: 'var(--color-severity-medium, #ca8a04)',
    low: 'var(--color-severity-low, #16a34a)',
    none: 'var(--color-primary, #2563eb)',
  };
  return colors[severity] || colors.none;
}

/**
 * Get device type icon shape.
 */
function getDeviceShape(deviceType?: string): string {
  const shapes: Record<string, string> = {
    router: 'diamond',
    switch: 'hexagon',
    server: 'rectangle',
    computer: 'round-rectangle',
    laptop: 'round-rectangle',
    phone: 'ellipse',
    printer: 'pentagon',
    camera: 'triangle',
    iot: 'star',
  };
  return shapes[deviceType || ''] || 'ellipse';
}

/**
 * Cytoscape stylesheet for network graph.
 */
// Cytoscape stylesheet - using type assertion because the strict types
// don't fully support dynamic data() expressions and all style properties
const cytoscapeStylesheet = [
  {
    selector: 'node',
    style: {
      'background-color': 'data(color)',
      'border-width': 2,
      'border-color': 'data(borderColor)',
      label: 'data(label)',
      'text-valign': 'bottom',
      'text-halign': 'center',
      'text-margin-y': 8,
      'font-size': 11,
      color: 'var(--color-foreground, #1f2937)',
      width: 40,
      height: 40,
      shape: 'data(shape)',
      'text-wrap': 'ellipsis',
      'text-max-width': 80,
    },
  },
  {
    selector: 'node:selected',
    style: {
      'border-width': 4,
      'border-color': 'var(--color-ring, #3b82f6)',
      'background-opacity': 1,
    },
  },
  {
    selector: 'node.gateway',
    style: {
      width: 60,
      height: 60,
      'font-weight': 'bold',
      'font-size': 12,
    },
  },
  {
    selector: 'node.offline',
    style: {
      opacity: 0.5,
      'border-style': 'dashed',
    },
  },
  {
    selector: 'edge',
    style: {
      width: 2,
      'line-color': 'var(--color-border, #e5e7eb)',
      'curve-style': 'bezier',
      opacity: 0.6,
    },
  },
  {
    selector: 'edge:selected',
    style: {
      'line-color': 'var(--color-primary, #2563eb)',
      width: 3,
      opacity: 1,
    },
  },
];

/**
 * NetworkGraph component for visualizing network topology.
 *
 * @example
 * ```tsx
 * <NetworkGraph
 *   devices={devices}
 *   selectedDeviceId={selectedId}
 *   onDeviceSelect={handleSelect}
 *   gatewayIp="192.168.1.1"
 * />
 * ```
 */
export function NetworkGraph({
  devices,
  selectedDeviceId,
  onDeviceSelect,
  onDeviceDoubleClick,
  gatewayIp,
  showLegend = true,
  showControls = true,
  ariaLabel = 'Network topology graph',
}: NetworkGraphProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<Core | null>(null);
  const [isInitialized, setIsInitialized] = useState(false);

  /**
   * Convert devices to Cytoscape elements.
   */
  const getElements = useCallback(() => {
    const nodes = devices.map((device) => {
      const severity = getDeviceSeverity(device);
      const isGateway = device.ip === gatewayIp;

      return {
        data: {
          id: device.id,
          label: device.hostname || device.ip,
          ip: device.ip,
          deviceType: device.device_type,
          vulnerabilityCount: device.vulnerability_count,
          severity,
          color: getSeverityColor(severity),
          borderColor: device.is_up
            ? getSeverityColor(severity)
            : 'var(--color-muted, #9ca3af)',
          shape: getDeviceShape(device.device_type),
          device, // Store full device for event handlers
        },
        classes: [
          isGateway ? 'gateway' : '',
          !device.is_up ? 'offline' : '',
        ].filter(Boolean).join(' '),
      };
    });

    // Create edges from each device to the gateway
    const edges = gatewayIp
      ? devices
          .filter((d) => d.ip !== gatewayIp)
          .map((device) => {
            const gatewayDevice = devices.find((d) => d.ip === gatewayIp);
            if (!gatewayDevice) return null;
            return {
              data: {
                id: `edge-${device.id}`,
                source: gatewayDevice.id,
                target: device.id,
              },
            };
          })
          .filter(Boolean)
      : [];

    return { nodes, edges };
  }, [devices, gatewayIp]);

  /**
   * Initialize Cytoscape instance.
   */
  useEffect(() => {
    if (!containerRef.current) return;

    log.info('Initializing network graph', { deviceCount: devices.length });

    const elements = getElements();

    cyRef.current = cytoscape({
      container: containerRef.current,
      elements: [...elements.nodes, ...elements.edges] as cytoscape.ElementDefinition[],
      style: cytoscapeStylesheet as (cytoscape.StylesheetStyle | cytoscape.StylesheetCSS)[],
      layout: {
        name: 'concentric',
        concentric: (node: NodeSingular) => {
          // Gateway in center
          if (node.hasClass('gateway')) return 10;
          // Critical devices closer to center
          const severity = node.data('severity');
          if (severity === 'critical') return 7;
          if (severity === 'high') return 5;
          if (severity === 'medium') return 3;
          return 1;
        },
        levelWidth: () => 2,
        minNodeSpacing: 50,
        animate: false,
      },
      minZoom: 0.3,
      maxZoom: 3,
      wheelSensitivity: 0.3,
    });

    // Event handlers
    cyRef.current.on('tap', 'node', (event: EventObject) => {
      const device = event.target.data('device') as Device;
      log.debug('Node clicked', { deviceId: device.id });
      onDeviceSelect?.(device);
    });

    cyRef.current.on('dbltap', 'node', (event: EventObject) => {
      const device = event.target.data('device') as Device;
      log.debug('Node double-clicked', { deviceId: device.id });
      onDeviceDoubleClick?.(device);
    });

    cyRef.current.on('tap', (event: EventObject) => {
      if (event.target === cyRef.current) {
        // Clicked on background
        onDeviceSelect?.(null);
      }
    });

    setIsInitialized(true);
    log.info('Network graph initialized');

    return () => {
      cyRef.current?.destroy();
      cyRef.current = null;
      setIsInitialized(false);
    };
  }, [devices, getElements, onDeviceSelect, onDeviceDoubleClick]);

  /**
   * Update selected node.
   */
  useEffect(() => {
    if (!cyRef.current || !isInitialized) return;

    // Deselect all
    cyRef.current.nodes().unselect();

    // Select the specified node
    if (selectedDeviceId) {
      cyRef.current.getElementById(selectedDeviceId).select();
    }
  }, [selectedDeviceId, isInitialized]);

  /**
   * Zoom controls.
   */
  const handleZoomIn = useCallback(() => {
    if (!cyRef.current) return;
    cyRef.current.zoom(cyRef.current.zoom() * 1.3);
  }, []);

  const handleZoomOut = useCallback(() => {
    if (!cyRef.current) return;
    cyRef.current.zoom(cyRef.current.zoom() / 1.3);
  }, []);

  const handleFitView = useCallback(() => {
    if (!cyRef.current) return;
    cyRef.current.fit(undefined, 50);
  }, []);

  const handleCenter = useCallback(() => {
    if (!cyRef.current) return;
    cyRef.current.center();
  }, []);

  /**
   * Keyboard navigation.
   */
  const handleKeyDown = useCallback(
    (event: React.KeyboardEvent) => {
      if (!cyRef.current) return;

      switch (event.key) {
        case '+':
        case '=':
          handleZoomIn();
          break;
        case '-':
          handleZoomOut();
          break;
        case '0':
          handleFitView();
          break;
        case 'Escape':
          onDeviceSelect?.(null);
          break;
        case 'Tab': {
          event.preventDefault();
          const nodes = cyRef.current.nodes();
          const selected = cyRef.current.nodes(':selected');
          if (nodes.length === 0) break;

          let nextIndex = 0;
          if (selected.length > 0) {
            // Find current node index using filter
            const nodesArray = nodes.toArray();
            const currentIndex = nodesArray.findIndex(n => n.id() === selected[0].id());
            nextIndex = event.shiftKey
              ? (currentIndex - 1 + nodes.length) % nodes.length
              : (currentIndex + 1) % nodes.length;
          }

          const nextNode = nodes[nextIndex];
          nextNode.select();
          cyRef.current.center(nextNode);
          onDeviceSelect?.(nextNode.data('device'));
          break;
        }
        case 'Enter':
        case ' ': {
          const selected = cyRef.current.nodes(':selected');
          if (selected.length > 0) {
            onDeviceDoubleClick?.(selected[0].data('device'));
          }
          break;
        }
      }
    },
    [handleZoomIn, handleZoomOut, handleFitView, onDeviceSelect, onDeviceDoubleClick]
  );

  return (
    <div className={styles.container}>
      <div
        ref={containerRef}
        className={styles.graph}
        role="img"
        aria-label={ariaLabel}
        tabIndex={0}
        onKeyDown={handleKeyDown}
      />
      {showControls && (
        <NetworkControls
          onZoomIn={handleZoomIn}
          onZoomOut={handleZoomOut}
          onFitView={handleFitView}
          onCenter={handleCenter}
        />
      )}
      {showLegend && <NetworkLegend />}
      <div className="sr-only" aria-live="polite">
        {selectedDeviceId
          ? `Selected device: ${devices.find((d) => d.id === selectedDeviceId)?.hostname || selectedDeviceId}`
          : 'No device selected'}
      </div>
    </div>
  );
}
