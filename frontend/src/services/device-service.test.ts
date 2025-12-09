/**
 * Device service unit tests.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { deviceService } from './device-service';
import {
  mockFetch,
  mockFetchError,
  mockDevice,
  mockDevices,
  mockVulnerabilities,
} from '@/test/mocks';

describe('DeviceService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('list', () => {
    it('should list devices with pagination', async () => {
      const response = {
        items: mockDevices,
        total: 3,
        page: 1,
        page_size: 20,
        pages: 1,
      };
      mockFetch(response);

      const result = await deviceService.list({ page: 1, page_size: 20 });

      expect(global.fetch).toHaveBeenCalledTimes(1);
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.items).toHaveLength(3);
        expect(result.data.total).toBe(3);
      }
    });

    it('should filter devices by scan_id', async () => {
      const response = {
        items: [mockDevice],
        total: 1,
        page: 1,
        page_size: 20,
        pages: 1,
      };
      mockFetch(response);

      await deviceService.list({ scan_id: 'scan-1' });

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('scan_id=scan-1'),
        expect.any(Object)
      );
    });

    it('should filter devices with vulnerabilities', async () => {
      const response = {
        items: mockDevices.filter((d) => d.vulnerability_count > 0),
        total: 2,
        page: 1,
        page_size: 20,
        pages: 1,
      };
      mockFetch(response);

      const result = await deviceService.list({ has_vulnerabilities: true });

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('has_vulnerabilities=true'),
        expect.any(Object)
      );
      expect(result.success).toBe(true);
    });
  });

  describe('get', () => {
    it('should fetch a single device by ID', async () => {
      mockFetch(mockDevice);

      const result = await deviceService.get('device-1');

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/devices/device-1'),
        expect.any(Object)
      );
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.id).toBe('device-1');
        expect(result.data.ip).toBe('192.168.1.1');
      }
    });

    it('should return error for non-existent device', async () => {
      mockFetchError('Device not found', 404);

      const result = await deviceService.get('non-existent');

      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.status_code).toBe(404);
      }
    });
  });

  describe('update', () => {
    it('should update device information', async () => {
      const updatedDevice = { ...mockDevice, hostname: 'new-hostname' };
      mockFetch(updatedDevice);

      const result = await deviceService.update('device-1', {
        hostname: 'new-hostname',
      });

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/devices/device-1'),
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify({ hostname: 'new-hostname' }),
        })
      );
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.hostname).toBe('new-hostname');
      }
    });
  });

  describe('delete', () => {
    it('should delete a device', async () => {
      mockFetch({ message: 'Device deleted' });

      const result = await deviceService.delete('device-1');

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/devices/device-1'),
        expect.objectContaining({ method: 'DELETE' })
      );
      expect(result.success).toBe(true);
    });
  });

  describe('getVulnerabilities', () => {
    it('should fetch vulnerabilities for a device', async () => {
      mockFetch(mockVulnerabilities);

      const result = await deviceService.getVulnerabilities('device-1');

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/devices/device-1/vulnerabilities'),
        expect.any(Object)
      );
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data).toHaveLength(3);
      }
    });
  });

  describe('getByScan', () => {
    it('should fetch devices for a specific scan', async () => {
      const response = {
        items: mockDevices,
        total: 3,
        page: 1,
        page_size: 20,
        pages: 1,
      };
      mockFetch(response);

      await deviceService.getByScan('scan-1');

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('scan_id=scan-1'),
        expect.any(Object)
      );
    });
  });

  describe('getVulnerable', () => {
    it('should fetch only vulnerable devices', async () => {
      const response = {
        items: mockDevices.filter((d) => d.vulnerability_count > 0),
        total: 2,
        page: 1,
        page_size: 20,
        pages: 1,
      };
      mockFetch(response);

      await deviceService.getVulnerable();

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('has_vulnerabilities=true'),
        expect.any(Object)
      );
    });
  });

  describe('count', () => {
    it('should return device count', async () => {
      mockFetch({
        items: [],
        total: 15,
        page: 1,
        page_size: 1,
        pages: 15,
      });

      const result = await deviceService.count();

      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data).toBe(15);
      }
    });
  });
});
