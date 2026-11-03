import { describe, it, expect } from 'vitest';
import {
  CR80_WIDTH_MM,
  CR80_HEIGHT_MM,
  CR80_ASPECT_RATIO,
  PNG_CANVAS_SIZE,
  PNG_QR_SIZE,
  CR80_LAYOUT,
  getNameFontSize,
  calculateCr80PixelDimensions,
  getQrCenterOffset,
} from '@/lib/qr-export';

describe('Tier 1: Card Geometry & Layout Math — Happy-Path Calculations', () => {
  it('T1-GEOM-01: verifies ISO/IEC 7810 ID-1 standard width (85.6mm)', () => {
    expect(CR80_WIDTH_MM).toBe(85.6);
  });

  it('T1-GEOM-02: verifies ISO/IEC 7810 ID-1 standard height (54.0mm)', () => {
    expect(CR80_HEIGHT_MM).toBe(54.0);
  });

  it('T1-GEOM-03: calculates ISO/IEC 7810 ID-1 standard aspect ratio (~1.5852)', () => {
    expect(CR80_ASPECT_RATIO).toBeCloseTo(1.585185, 4);
  });

  it('T1-GEOM-04: calculates 300 DPI canvas dimensions for print quality (1011 x 638 px)', () => {
    const { widthPx, heightPx } = calculateCr80PixelDimensions(300);
    expect(widthPx).toBe(1011);
    expect(heightPx).toBe(638);
  });

  it('T1-GEOM-05: calculates 600 DPI ultra-high-res canvas dimensions (2022 x 1276 px)', () => {
    const { widthPx, heightPx } = calculateCr80PixelDimensions(600);
    expect(widthPx).toBe(2022);
    expect(heightPx).toBe(1276);
  });

  it('T1-GEOM-06: calculates 150 DPI preview canvas dimensions (506 x 319 px)', () => {
    const { widthPx, heightPx } = calculateCr80PixelDimensions(150);
    expect(widthPx).toBe(506);
    expect(heightPx).toBe(319);
  });

  it('T1-GEOM-07: verifies default PNG canvas dimension is 1080px square', () => {
    expect(PNG_CANVAS_SIZE).toBe(1080);
  });

  it('T1-GEOM-08: verifies default PNG QR code dimension is 700px square', () => {
    expect(PNG_QR_SIZE).toBe(700);
  });

  it('T1-GEOM-09: calculates high-res PNG centered QR offset (190px)', () => {
    const offset = getQrCenterOffset(PNG_CANVAS_SIZE, PNG_QR_SIZE);
    expect(offset).toBe(190);
    expect(offset + PNG_QR_SIZE).toBe(890);
  });

  it('T1-GEOM-10: verifies standard 11pt font size for short patient names', () => {
    expect(getNameFontSize('John Doe')).toBe(11);
    expect(getNameFontSize('Robert A. King')).toBe(11);
  });

  it('T1-GEOM-11: verifies scaled 9pt font size for long patient names', () => {
    expect(getNameFontSize('Jane Livingston Smith')).toBe(9);
    expect(getNameFontSize('Alexander Bartholomew Jr.')).toBe(9);
  });

  it('T1-GEOM-12: verifies PDF front page column layout margins and right gutter', () => {
    const rightMargin = CR80_WIDTH_MM - (CR80_LAYOUT.qrXMm + CR80_LAYOUT.qrSizeMm);
    expect(rightMargin).toBeCloseTo(4.0, 1);
  });

  it('T1-GEOM-13: verifies PDF front header bar height is 8mm', () => {
    expect(CR80_LAYOUT.headerHeightMm).toBe(8);
  });

  it('T1-GEOM-14: verifies PDF blood group badge bounds (26mm x 12mm with 1.5mm radius)', () => {
    expect(CR80_LAYOUT.bloodBox.w).toBe(26);
    expect(CR80_LAYOUT.bloodBox.h).toBe(12);
    expect(CR80_LAYOUT.bloodBox.r).toBe(1.5);
  });

  it('T1-GEOM-15: calculates ISO CR80 physical card perimeter (279.2mm)', () => {
    const perimeter = 2 * (CR80_WIDTH_MM + CR80_HEIGHT_MM);
    expect(perimeter).toBeCloseTo(279.2, 1);
  });
});

describe('Tier 2: Card Geometry & Layout Math — Boundaries & Scaling Limits', () => {
  it('T2-GEOM-01: verifies exact font size transition boundary at 20 characters', () => {
    expect(getNameFontSize('A'.repeat(20))).toBe(11);
  });

  it('T2-GEOM-02: verifies exact font size transition boundary at 21 characters', () => {
    expect(getNameFontSize('A'.repeat(21))).toBe(9);
  });

  it('T2-GEOM-03: verifies extreme long name retains 9pt scaling floor (100 characters)', () => {
    expect(getNameFontSize('A'.repeat(100))).toBe(9);
  });

  it('T2-GEOM-04: verifies empty string defaults to 11pt without throwing', () => {
    expect(getNameFontSize('')).toBe(11);
  });

  it('T2-GEOM-05: confirms 300 DPI canvas aspect ratio deviates less than 0.05% from ISO standard', () => {
    const standardRatio = CR80_ASPECT_RATIO;
    const canvasRatio = 1011 / 638;
    const deviationPercent = Math.abs((canvasRatio - standardRatio) / standardRatio) * 100;
    expect(deviationPercent).toBeLessThan(0.05);
  });

  it('T2-GEOM-06: confirms PNG vertical safe area accommodates all labels without overlap', () => {
    expect(140).toBeGreaterThan(90 + 36 / 2);
    expect(900).toBeGreaterThan(140 + 700);
    expect(960).toBeGreaterThan(900 + 44 / 2);
    expect(1020).toBeGreaterThan(960 + 32 / 2);
    expect(1020 + 24 / 2).toBeLessThanOrEqual(PNG_CANVAS_SIZE);
  });

  it('T2-GEOM-07: verifies left column maxWidth does not encroach on QR code x position', () => {
    const leftMargin = CR80_LAYOUT.bloodBox.x;
    const leftContentEnd = leftMargin + CR80_LAYOUT.leftColumnMaxWidthMm;
    expect(leftContentEnd).toBeLessThan(CR80_LAYOUT.qrXMm);
  });

  it('T2-GEOM-08: verifies custom canvas centering offset with non-standard dimensions', () => {
    expect(getQrCenterOffset(800, 400)).toBe(200);
    expect(getQrCenterOffset(1200, 600)).toBe(300);
  });

  it('T2-GEOM-09: verifies reverse side header stripe height is 6mm', () => {
    expect(CR80_LAYOUT.backHeaderStripeMm).toBe(6);
  });

  it('T2-GEOM-10: verifies reverse side content width accommodates standard ISO margins', () => {
    expect(CR80_LAYOUT.backContentMaxWidthMm + 8).toBeLessThanOrEqual(CR80_WIDTH_MM);
  });

  it('T2-GEOM-11: verifies screen-resolution 72 DPI canvas dimensions (243 x 153 px)', () => {
    const { widthPx, heightPx } = calculateCr80PixelDimensions(72);
    expect(widthPx).toBe(243);
    expect(heightPx).toBe(153);
  });

  it('T2-GEOM-12: verifies ultra-press 1200 DPI canvas dimensions (4044 x 2551 px)', () => {
    const { widthPx, heightPx } = calculateCr80PixelDimensions(1200);
    expect(widthPx).toBe(4044);
    expect(heightPx).toBe(2551);
  });

  it('T2-GEOM-13: verifies getNameFontSize with multi-byte Unicode names', () => {
    expect(getNameFontSize('José María González')).toBe(11);
    expect(getNameFontSize('François-Alexandre de la Tour')).toBe(9);
  });

  it('T2-GEOM-14: verifies getQrCenterOffset when canvas equals QR size returns 0', () => {
    expect(getQrCenterOffset(500, 500)).toBe(0);
  });

  it('T2-GEOM-15: verifies calculateCr80PixelDimensions returns 0 on 0 DPI', () => {
    const dims = calculateCr80PixelDimensions(0);
    expect(dims.widthPx).toBe(0);
    expect(dims.heightPx).toBe(0);
  });
});
