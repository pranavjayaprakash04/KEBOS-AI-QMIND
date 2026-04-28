import { renderHook, waitFor } from '@testing-library/react';
import { useBackendHealth } from './useBackendHealth';

// Mock fetch
global.fetch = jest.fn();

describe('useBackendHealth', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should start with checking status', () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
    });

    const { result } = renderHook(() => useBackendHealth(1000));
    expect(result.current).toBe('checking');
  });

  it('should return healthy when backend responds with 200', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
    });

    const { result } = renderHook(() => useBackendHealth(100));

    await waitFor(() => {
      expect(result.current).toBe('healthy');
    });
  });

  it('should return unhealthy when backend responds with error', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
    });

    const { result } = renderHook(() => useBackendHealth(100));

    await waitFor(() => {
      expect(result.current).toBe('unhealthy');
    });
  });

  it('should return unhealthy when fetch fails', async () => {
    (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

    const { result } = renderHook(() => useBackendHealth(100));

    await waitFor(() => {
      expect(result.current).toBe('unhealthy');
    });
  });

  it('should poll health status at specified interval', async () => {
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({ ok: true })
      .mockResolvedValueOnce({ ok: false });

    const { result } = renderHook(() => useBackendHealth(100));

    await waitFor(() => {
      expect(result.current).toBe('healthy');
    });

    await waitFor(() => {
      expect(result.current).toBe('unhealthy');
    }, { timeout: 300 });
  });

  it('should timeout after 5 seconds', async () => {
    (global.fetch as jest.Mock).mockImplementation(() => 
      new Promise((resolve) => setTimeout(() => resolve({ ok: true }), 6000))
    );

    const { result } = renderHook(() => useBackendHealth(100));

    await waitFor(() => {
      expect(result.current).toBe('unhealthy');
    }, { timeout: 6000 });
  });
});
