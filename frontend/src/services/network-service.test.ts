/**
 * Network service unit tests.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { networkService } from './network-service';
import {
  mockFetch,
  mockFetchError,
  mockScanResponse,
  mockScanStatus,
  mockNetworkInterface,
} from '@/test/mocks';
import type { ScanRequest, NetworkValidationResponse } from '@/types';

describe('NetworkService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('startScan', () => {
    it('should start a scan and return response', async () => {
      mockFetch(mockScanResponse);

      const request: ScanRequest = {
        target: '192.168.1.0/24',
        scan_type: 'quick',
        user_consent: true,
      };

      const result = await networkService.startScan(request);

      expect(global.fetch).toHaveBeenCalledTimes(1);
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.scan_id).toBe('scan-1');
        expect(result.data.target_range).toBe('192.168.1.0/24');
      }
    });

    it('should handle scan start failure', async () => {
      mockFetchError('Invalid target', 400);

      const result = await networkService.startScan({
        target: 'invalid',
        scan_type: 'quick',
        user_consent: true,
      });

      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.detail).toBe('Invalid target');
      }
    });
  });

  describe('getScan', () => {
    it('should fetch scan results by ID', async () => {
      mockFetch(mockScanResponse);

      const result = await networkService.getScan('scan-1');

      expect(global.fetch).toHaveBeenCalledTimes(1);
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.devices).toHaveLength(3);
      }
    });
  });

  describe('getScanStatus', () => {
    it('should fetch scan status', async () => {
      mockFetch(mockScanStatus);

      const result = await networkService.getScanStatus('scan-1');

      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.progress).toBe(50);
        expect(result.data.status).toBe('running');
      }
    });
  });

  describe('cancelScan', () => {
    it('should cancel a running scan', async () => {
      mockFetch({ message: 'Scan cancelled' });

      const result = await networkService.cancelScan('scan-1');

      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.message).toBe('Scan cancelled');
      }
    });
  });

  describe('getInterfaces', () => {
    it('should list network interfaces', async () => {
      mockFetch([mockNetworkInterface]);

      const result = await networkService.getInterfaces();

      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data).toHaveLength(1);
        expect(result.data[0].name).toBe('eth0');
      }
    });
  });

  describe('detectNetwork', () => {
    it('should auto-detect network', async () => {
      mockFetch(mockNetworkInterface);

      const result = await networkService.detectNetwork();

      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.network).toBe('192.168.1.0/24');
        expect(result.data.is_private).toBe(true);
      }
    });
  });

  describe('validateTarget', () => {
    it('should validate a valid target', async () => {
      const validation: NetworkValidationResponse = {
        valid: true,
        target: '192.168.1.0/24',
        is_private: true,
        num_hosts: 254,
        type: 'network',
      };
      mockFetch(validation);

      const result = await networkService.validateTarget({
        target: '192.168.1.0/24',
      });

      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.valid).toBe(true);
        expect(result.data.num_hosts).toBe(254);
      }
    });

    it('should return validation error for invalid target', async () => {
      const validation: NetworkValidationResponse = {
        valid: false,
        target: '8.8.8.8',
        is_private: false,
        num_hosts: 1,
        type: 'single_ip',
        error: 'Not a private network',
      };
      mockFetch(validation);

      const result = await networkService.validateTarget({ target: '8.8.8.8' });

      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.valid).toBe(false);
        expect(result.data.error).toBe('Not a private network');
      }
    });
  });

  describe('listScans', () => {
    it('should list scans with pagination', async () => {
      const response = {
        items: [mockScanResponse],
        total: 1,
        page: 1,
        page_size: 20,
        pages: 1,
      };
      mockFetch(response);

      const result = await networkService.listScans({ page: 1, page_size: 20 });

      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.items).toHaveLength(1);
        expect(result.data.total).toBe(1);
      }
    });
  });
});
