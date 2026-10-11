import { expect, test, type Page } from '@playwright/test';

const SENTIMENT_RESPONSE = {
  polarity: 0.4117,
  subjectivity: 0.375,
  classification: 'positive',
  positivityScore: 0.7,
  negativityScore: 0.0,
  neutralityScore: 0.3,
  compoundScore: 0.4117,
  isDivergent: false,
  emotions: {
    joy: 0.19,
    sadness: 0.0,
    anger: 0.0,
    fear: 0.0,
    trust: 0.1,
    surprise: 0.0,
    disgust: 0.0,
    anticipation: 0.05
  },
  sentenceBreakdown: [
    { index: 0, text: 'Sample.', polarity: 0.4, subjectivity: 0.3, classification: 'positive' }
  ]
};

const READABILITY_RESPONSE = {
  fleschReadingEase: 71.4,
  fleschKincaidGrade: 6.2,
  gunningFogIndex: 8.4,
  colemanLiauIndex: 9.1,
  smogIndex: 7.3,
  automatedReadabilityIndex: 6.8,
  readingTimeSeconds: 30,
  speakingTimeSeconds: 60,
  syllableCount: 120,
  complexWordCount: 6,
  gradeLevelConsensus: 'Grade 7.6',
  cefrEquivalent: 'B1',
  sentenceBreakdown: [
    {
      index: 0,
      text: 'Sample.',
      wordCount: 9,
      syllableCount: 12,
      characterCount: 41,
      complexWordCount: 1,
      readingEase: 71.4,
      isExtremelyLong: false
    }
  ]
};

async function mockAnalysisApi(page: Page, options: { latency?: number } = {}) {
  const latency = options.latency ?? 0;
  await page.route('**/api/v1/sentiment/analyze', async (route) => {
    if (latency > 0) await new Promise((resolve) => setTimeout(resolve, latency));
    await route.fulfill({ json: SENTIMENT_RESPONSE });
  });
  await page.route('**/api/v1/readability/analyze', async (route) => {
    if (latency > 0) await new Promise((resolve) => setTimeout(resolve, latency));
    await route.fulfill({ json: READABILITY_RESPONSE });
  });
}

test.describe('Workbench responsive layout', () => {
  for (const width of [360, 390, 430, 768, 1280]) {
    test(`renders without horizontal scroll at ${width}px viewport`, async ({ page }) => {
      await mockAnalysisApi(page);
      await page.setViewportSize({ width, height: 900 });
      await page.goto('/');
      await expect(page.getByRole('heading', { name: 'The Manuscript Review' })).toBeVisible();

      const metrics = await page.evaluate(() => ({
        scrollWidth: document.scrollingElement ? document.scrollingElement.scrollWidth : 0,
        clientWidth: document.scrollingElement ? document.scrollingElement.clientWidth : 0
      }));
      expect(metrics.scrollWidth).toBeLessThanOrEqual(metrics.clientWidth);
    });
  }
});

test.describe('Analysis dispatch', () => {
  test('submits text, shows loading state, and renders metrics without Not Found', async ({
    page
  }) => {
    await mockAnalysisApi(page, { latency: 2500 });
    await page.goto('/');

    const textarea = page.locator('textarea');
    await textarea.fill('The clarity of the prose carries the argument with remarkable force.');
    await expect(textarea).toHaveValue(/clarity of the prose/);

    const runButton = page.getByRole('button', { name: /Run Analysis|Evaluating Text/ });
    await runButton.click();
    const analyzing = page.getByRole('button', { name: 'Evaluating Text...' });
    await expect(analyzing).toBeVisible();
    await expect(analyzing).toBeDisabled();

    await expect(page.getByRole('heading', { name: 'Sentiment Evaluation' })).toBeVisible({
      timeout: 10_000
    });
    await expect(page.getByRole('heading', { name: 'Emotion Spectrum' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Readability Standard' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Metric Grid' })).toBeVisible();
    await expect(page.getByText('Not Found')).toHaveCount(0);
    await expect(page.getByText('B1').first()).toBeVisible();
  });

  test('rapid consecutive dispatches do not corrupt results', async ({ page }) => {
    await mockAnalysisApi(page, { latency: 300 });
    await page.goto('/');
    const textarea = page.locator('textarea');
    await textarea.fill('First dispatch.');
    const runButton = page.getByRole('button', { name: 'Run Analysis' });
    await runButton.click();
    await textarea.fill('Second dispatch with more distinctive content.');
    await runButton.click();

    await expect(page.getByRole('heading', { name: 'Sentiment Evaluation' })).toBeVisible({
      timeout: 10_000
    });
    await expect(page.getByText('Not Found')).toHaveCount(0);
  });
});

test.describe('Field Guide modal', () => {
  test('opens from the header, displays all sections, and closes with keyboard', async ({
    page
  }) => {
    await mockAnalysisApi(page);
    await page.goto('/');

    const guideButton = page.getByRole('button', { name: 'Field Guide' }).first();
    await expect(guideButton).toBeVisible();
    const box = await guideButton.boundingBox();
    expect(box).not.toBeNull();
    expect(box!.height).toBeGreaterThanOrEqual(44);
    expect(box!.width).toBeGreaterThanOrEqual(44);

    await guideButton.click();
    const dialog = page.getByRole('dialog', { name: "Editorial Reader's Field Guide" });
    await expect(dialog).toBeVisible();
    await expect(dialog.getByText('Purpose')).toBeVisible();
    await expect(dialog.getByText('Navigating the Desk')).toBeVisible();
    await expect(dialog.getByText('Metrics Interpretation')).toBeVisible();
    await expect(dialog.getByText('Friction Markers')).toBeVisible();
    await expect(dialog.getByText('Flesch Reading Ease')).toBeVisible();
    await expect(dialog.getByText('CEFR Grade Consensus')).toBeVisible();
    await expect(dialog.getByText('Gunning Fog Index')).toBeVisible();
    await expect(dialog.getByText('Polarity Compound Score')).toBeVisible();
    await expect(dialog.getByText('Plutchik Emotion Radar')).toBeVisible();

    const closeButton = dialog.getByRole('button', { name: 'Close field guide' });
    const closeBox = await closeButton.boundingBox();
    expect(closeBox).not.toBeNull();
    expect(closeBox!.height).toBeGreaterThanOrEqual(44);
    expect(closeBox!.width).toBeGreaterThanOrEqual(44);

    await page.keyboard.press('Escape');
    await expect(dialog).toBeHidden();
  });

  test('opens from the composition pane and closes via backdrop button', async ({ page }) => {
    await mockAnalysisApi(page);
    await page.goto('/');
    await page.getByRole('button', { name: 'Field Guide' }).last().click();
    const dialog = page.getByRole('dialog', { name: "Editorial Reader's Field Guide" });
    await expect(dialog).toBeVisible();
    await closeButton(dialog, page);
    await expect(dialog).toBeHidden();
  });

  async function closeButton(dialog: ReturnType<Page['getByRole']>, page: Page) {
    await dialog.getByRole('button', { name: 'Close field guide' }).click();
    void page;
  }
});

test.describe('Offline archive', () => {
  const seedDocument = {
    id: 'seed-1',
    title: 'Seeded Offline Manuscript',
    wordCount: 55,
    characterCount: 330,
    sentenceCount: 4,
    paragraphCount: 1,
    sentimentClassification: 'positive',
    cefrEquivalent: 'B2',
    createdAt: '2026-01-10T12:00:00Z'
  };

  test('lists and deletes seeded offline documents while the API is unreachable', async ({
    page
  }) => {
    await page.addInitScript((doc) => {
      if (localStorage.getItem('seed-applied') === '1') return;
      localStorage.setItem('seed-applied', '1');
      const open = indexedDB.open('text-analysis-archive', 1);
      open.onupgradeneeded = () => {
        const db = open.result;
        if (!db.objectStoreNames.contains('documents')) {
          db.createObjectStore('documents', { keyPath: 'id' });
        }
      };
      open.onsuccess = () => {
        const db = open.result;
        const tx = db.transaction('documents', 'readwrite');
        tx.objectStore('documents').put(doc);
      };
    }, seedDocument);

    // Simulate total network failure for the archive API.
    await page.route('**/api/v1/history**', (route) => route.abort());

    await page.goto('/history');
    const offlineBadge = page.getByText('Offline', { exact: false }).first();
    await expect(offlineBadge).toBeVisible();
    await expect(page.getByText('Seeded Offline Manuscript')).toBeVisible();

    // Touch-target check on the delete control.
    const deleteButton = page.getByRole('button', { name: 'Delete' }).first();
    const box = await deleteButton.boundingBox();
    expect(box).not.toBeNull();
    expect(box!.height).toBeGreaterThanOrEqual(44);
    expect(box!.width).toBeGreaterThanOrEqual(44);

    await deleteButton.click();
    await expect(page.getByText('Seeded Offline Manuscript')).toHaveCount(0);

    // The deletion is persisted in the local mirror: reload and confirm.
    await page.reload();
    await expect(page.getByText('Seeded Offline Manuscript')).toHaveCount(0);
  });
});
