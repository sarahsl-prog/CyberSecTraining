/**
 * Vitest test setup file.
 *
 * Configures the test environment with necessary globals and mocks.
 */

import '@testing-library/jest-dom';
import { vi } from 'vitest';

// Mock fetch globally
global.fetch = vi.fn();

// Mock ResizeObserver (not available in jsdom)
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}));

// Mock matchMedia (not available in jsdom)
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

// Mock HTMLDialogElement (not fully supported in jsdom)
if (typeof HTMLDialogElement === 'undefined') {
  (global as any).HTMLDialogElement = class HTMLDialogElement extends HTMLElement {
    open = false;
    returnValue = '';

    showModal() {
      this.open = true;
    }

    close(returnValue?: string) {
      this.open = false;
      if (returnValue !== undefined) {
        this.returnValue = returnValue;
      }
    }

    show() {
      this.open = true;
    }
  };
} else {
  // Polyfill methods if they don't exist
  if (!HTMLDialogElement.prototype.showModal) {
    HTMLDialogElement.prototype.showModal = function() {
      this.setAttribute('open', '');
    };
  }

  if (!HTMLDialogElement.prototype.close) {
    HTMLDialogElement.prototype.close = function() {
      this.removeAttribute('open');
    };
  }
}

// Reset mocks between tests
beforeEach(() => {
  vi.clearAllMocks();
  localStorageMock.getItem.mockReturnValue(null);
});
