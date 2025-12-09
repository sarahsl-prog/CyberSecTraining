/**
 * NetworkControls component.
 *
 * Provides zoom and pan controls for the network graph visualization.
 * Accessible with keyboard shortcuts and screen reader support.
 */

import { Button } from '@/components/common';
import styles from './NetworkControls.module.css';

/**
 * Props for NetworkControls component.
 */
export interface NetworkControlsProps {
  /** Zoom in handler */
  onZoomIn: () => void;
  /** Zoom out handler */
  onZoomOut: () => void;
  /** Fit view handler */
  onFitView: () => void;
  /** Center view handler */
  onCenter: () => void;
}

/**
 * NetworkControls component for graph navigation.
 *
 * Keyboard shortcuts:
 * - + or = : Zoom in
 * - - : Zoom out
 * - 0 : Fit view
 * - Tab : Navigate between nodes
 * - Enter/Space : Open device details
 * - Escape : Deselect
 *
 * @example
 * ```tsx
 * <NetworkControls
 *   onZoomIn={handleZoomIn}
 *   onZoomOut={handleZoomOut}
 *   onFitView={handleFitView}
 *   onCenter={handleCenter}
 * />
 * ```
 */
export function NetworkControls({
  onZoomIn,
  onZoomOut,
  onFitView,
  onCenter,
}: NetworkControlsProps) {
  return (
    <div className={styles.controls} role="toolbar" aria-label="Graph controls">
      <div className={styles.group}>
        <Button
          variant="outline"
          size="sm"
          onClick={onZoomIn}
          aria-label="Zoom in (keyboard: +)"
          title="Zoom in (+)"
        >
          <ZoomInIcon />
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={onZoomOut}
          aria-label="Zoom out (keyboard: -)"
          title="Zoom out (-)"
        >
          <ZoomOutIcon />
        </Button>
      </div>
      <div className={styles.group}>
        <Button
          variant="outline"
          size="sm"
          onClick={onFitView}
          aria-label="Fit all nodes in view (keyboard: 0)"
          title="Fit view (0)"
        >
          <FitViewIcon />
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={onCenter}
          aria-label="Center view"
          title="Center view"
        >
          <CenterIcon />
        </Button>
      </div>
    </div>
  );
}

// Icon components
function ZoomInIcon() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <circle cx="11" cy="11" r="8" />
      <line x1="21" y1="21" x2="16.65" y2="16.65" />
      <line x1="11" y1="8" x2="11" y2="14" />
      <line x1="8" y1="11" x2="14" y2="11" />
    </svg>
  );
}

function ZoomOutIcon() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <circle cx="11" cy="11" r="8" />
      <line x1="21" y1="21" x2="16.65" y2="16.65" />
      <line x1="8" y1="11" x2="14" y2="11" />
    </svg>
  );
}

function FitViewIcon() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M8 3H5a2 2 0 0 0-2 2v3" />
      <path d="M21 8V5a2 2 0 0 0-2-2h-3" />
      <path d="M3 16v3a2 2 0 0 0 2 2h3" />
      <path d="M16 21h3a2 2 0 0 0 2-2v-3" />
    </svg>
  );
}

function CenterIcon() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <circle cx="12" cy="12" r="3" />
      <path d="M12 2v4" />
      <path d="M12 18v4" />
      <path d="M2 12h4" />
      <path d="M18 12h4" />
    </svg>
  );
}
