/**
 * Тести для API модуля
 * Запуск: npm test
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { fetchTransactions, fetchStats } from './api';

// Mock global fetch
global.fetch = vi.fn();

describe('API Tests', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  describe('fetchTransactions', () => {
    it('should fetch transactions successfully', async () => {
      const mockTransactions = [
        { _id: '1', uid: 'A1B2C3D4', status: 'GRANTED', timestamp: 1234567890 },
        { _id: '2', uid: 'DEADBEEF', status: 'DENIED', timestamp: 1234567891 }
      ];

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockTransactions
      });

      const result = await fetchTransactions(100);
      
      expect(result).toEqual(mockTransactions);
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/transactions?limit=100'),
        expect.objectContaining({ credentials: 'include' })
      );
    });

    it('should throw error on failed fetch', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 500
      });

      await expect(fetchTransactions()).rejects.toThrow('Failed to fetch transactions: 500');
    });

    it('should use default limit if not provided', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => []
      });

      await fetchTransactions();
      
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('limit=100'),
        expect.any(Object)
      );
    });
  });

  describe('fetchStats', () => {
    it('should fetch stats successfully', async () => {
      const mockStats = {
        since: 1234567890,
        now: 1234571490,
        total: { GRANTED: 10, DENIED: 5 },
        timeline: [
          { t: 1234567890, granted: 5, denied: 2 },
          { t: 1234571490, granted: 5, denied: 3 }
        ]
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockStats
      });

      const result = await fetchStats(24);
      
      expect(result).toEqual(mockStats);
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/stats?hours=24'),
        expect.objectContaining({ credentials: 'include' })
      );
    });

    it('should throw error on failed fetch', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 404
      });

      await expect(fetchStats()).rejects.toThrow('Failed to fetch stats: 404');
    });

    it('should use default hours if not provided', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ since: 0, now: 0, total: {}, timeline: [] })
      });

      await fetchStats();
      
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('hours=24'),
        expect.any(Object)
      );
    });
  });
});

