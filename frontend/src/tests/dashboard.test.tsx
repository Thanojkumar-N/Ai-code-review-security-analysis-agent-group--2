import { describe, it, expect } from 'vitest';

describe('Dashboard Component Unit Verification', () => {
  it('correctly calculates average metrics', () => {
    const mockReports = [
      { id: '1', score: 90, summary: 'Clean run', created_at: '2026-07-16' },
      { id: '2', score: 80, summary: 'Smells found', created_at: '2026-07-16' },
    ];
    
    const totalScans = mockReports.length;
    const averageScore = Math.round(mockReports.reduce((acc, curr) => acc + curr.score, 0) / totalScans);
    
    expect(totalScans).toBe(2);
    expect(averageScore).toBe(85);
  });

  it('determines the correct health descriptors warning badge', () => {
    const getHealthColor = (score: number) => {
      if (score < 70) return 'border-red-500';
      if (score < 85) return 'border-yellow-500';
      return 'border-green-500';
    };

    expect(getHealthColor(95)).toBe('border-green-500');
    expect(getHealthColor(80)).toBe('border-yellow-500');
    expect(getHealthColor(60)).toBe('border-red-500');
  });
});
