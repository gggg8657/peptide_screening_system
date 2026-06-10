import { chromium } from 'playwright';

const OUTDIR = '/Users/gimdongju/Documents/workspace/secu/PRST_N_FM/docs/screenshots';
const BASE = 'http://localhost:5173';

async function captureElement(page, selector, filename, fallbackClip) {
  try {
    const el = page.locator(selector).first();
    if (await el.count()) {
      await el.scrollIntoViewIfNeeded();
      await page.waitForTimeout(600);
      await el.screenshot({ path: `${OUTDIR}/${filename}` });
      console.log(`✅ ${filename}`);
      return true;
    }
  } catch (e) { /* fall through */ }
  if (fallbackClip) {
    await page.screenshot({ path: `${OUTDIR}/${filename}`, clip: fallbackClip });
    console.log(`✅ ${filename} (clip)`);
    return true;
  }
  console.log(`⏭️ ${filename}: not found`);
  return false;
}

async function main() {
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 2 });
  const page = await ctx.newPage();

  // ========== Silo B ==========
  await page.goto(`${BASE}/silo-b`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(2500);

  // Full page
  await page.screenshot({ path: `${OUTDIR}/01_silo_b_full.png`, fullPage: true });
  console.log('✅ 01_silo_b_full');

  // Header + Pipeline Status (top area)
  await page.screenshot({ path: `${OUTDIR}/02_header_pipeline.png`, clip: { x: 0, y: 0, width: 1440, height: 220 } });
  console.log('✅ 02_header_pipeline');

  // ExperimentControl - look for the specific component
  await captureElement(page, '[class*="experiment"], [data-testid="experiment-control"]', '03_experiment_control.png',
    { x: 0, y: 220, width: 1440, height: 450 });

  // Agent Monitor + Candidate Table side by side
  await captureElement(page, 'text=AGENT MONITOR', 'skip', null);
  const agentEl = page.locator('text=AGENT MONITOR').first();
  if (await agentEl.count()) {
    await agentEl.scrollIntoViewIfNeeded();
    await page.waitForTimeout(300);
    const box = await agentEl.boundingBox();
    if (box) {
      await page.screenshot({ path: `${OUTDIR}/04_agent_and_candidates.png`,
        clip: { x: 0, y: Math.max(0, box.y - 10), width: 1440, height: 520 } });
      console.log('✅ 04_agent_and_candidates');
    }
  }

  // CandidateTable only
  const tableEl = page.locator('text=CANDIDATE RANKING').first();
  if (await tableEl.count()) {
    await tableEl.scrollIntoViewIfNeeded();
    await page.waitForTimeout(300);
    const box = await tableEl.boundingBox();
    if (box) {
      await page.screenshot({ path: `${OUTDIR}/05_candidate_table.png`,
        clip: { x: 300, y: Math.max(0, box.y - 10), width: 1140, height: 550 } });
      console.log('✅ 05_candidate_table');
    }
  }

  // ddG Distribution
  const ddgEl = page.locator('text=ddG Distribution').first();
  if (await ddgEl.count()) {
    await ddgEl.scrollIntoViewIfNeeded();
    await page.waitForTimeout(500);
    const box = await ddgEl.boundingBox();
    if (box) {
      await page.screenshot({ path: `${OUTDIR}/06_ddg_distribution.png`,
        clip: { x: 0, y: Math.max(0, box.y - 20), width: 1440, height: 420 } });
      console.log('✅ 06_ddg_distribution');
    }
  }

  // Unified Validation
  const valEl = page.locator('text=Unified Validation').first();
  if (await valEl.count()) {
    await valEl.scrollIntoViewIfNeeded();
    await page.waitForTimeout(500);
    const box = await valEl.boundingBox();
    if (box) {
      await page.screenshot({ path: `${OUTDIR}/07_validation.png`,
        clip: { x: 0, y: Math.max(0, box.y - 20), width: 1440, height: 400 } });
      console.log('✅ 07_validation');
    }
  }

  // Pharmacology Panel
  const pharmEl = page.locator('text=Pharmacology').first();
  if (await pharmEl.count()) {
    await pharmEl.scrollIntoViewIfNeeded();
    await page.waitForTimeout(500);
    const box = await pharmEl.boundingBox();
    if (box) {
      await page.screenshot({ path: `${OUTDIR}/08_pharmacology.png`,
        clip: { x: 0, y: Math.max(0, box.y - 20), width: 1440, height: 500 } });
      console.log('✅ 08_pharmacology');
    }
  }

  // SAR Heatmap
  const sarEl = page.locator('text=SAR Heatmap').first();
  if (await sarEl.count()) {
    await sarEl.scrollIntoViewIfNeeded();
    await page.waitForTimeout(500);
    const box = await sarEl.boundingBox();
    if (box) {
      await page.screenshot({ path: `${OUTDIR}/09_sar_heatmap.png`,
        clip: { x: 0, y: Math.max(0, box.y - 20), width: 1440, height: 550 } });
      console.log('✅ 09_sar_heatmap');
    }
  }

  // Sequence Logo
  const logoEl = page.locator('text=Sequence Logo').first();
  if (await logoEl.count()) {
    await logoEl.scrollIntoViewIfNeeded();
    await page.waitForTimeout(500);
    const box = await logoEl.boundingBox();
    if (box) {
      await page.screenshot({ path: `${OUTDIR}/10_sequence_logo.png`,
        clip: { x: 0, y: Math.max(0, box.y - 20), width: 1440, height: 400 } });
      console.log('✅ 10_sequence_logo');
    }
  }

  // Mutation Analysis
  const mutEl = page.locator('text=Mutation Analysis').first();
  if (await mutEl.count()) {
    await mutEl.scrollIntoViewIfNeeded();
    await page.waitForTimeout(500);
    const box = await mutEl.boundingBox();
    if (box) {
      await page.screenshot({ path: `${OUTDIR}/11_mutation_analysis.png`,
        clip: { x: 0, y: Math.max(0, box.y - 20), width: 1440, height: 450 } });
      console.log('✅ 11_mutation_analysis');
    }
  }

  // Position Enrichment
  const posEl = page.locator('text=Position Enrichment').first();
  if (await posEl.count()) {
    await posEl.scrollIntoViewIfNeeded();
    await page.waitForTimeout(500);
    const box = await posEl.boundingBox();
    if (box) {
      await page.screenshot({ path: `${OUTDIR}/12_position_enrichment.png`,
        clip: { x: 0, y: Math.max(0, box.y - 20), width: 1440, height: 500 } });
      console.log('✅ 12_position_enrichment');
    }
  }

  // QC Gate + Convergence side by side
  const qcEl = page.locator('text=QC Gate').first();
  if (await qcEl.count()) {
    await qcEl.scrollIntoViewIfNeeded();
    await page.waitForTimeout(500);
    const box = await qcEl.boundingBox();
    if (box) {
      await page.screenshot({ path: `${OUTDIR}/13_qc_convergence.png`,
        clip: { x: 0, y: Math.max(0, box.y - 20), width: 1440, height: 420 } });
      console.log('✅ 13_qc_convergence');
    }
  }

  // Risk Matrix
  const riskEl = page.locator('text=Risk Matrix').first();
  if (await riskEl.count()) {
    await riskEl.scrollIntoViewIfNeeded();
    await page.waitForTimeout(500);
    const box = await riskEl.boundingBox();
    if (box) {
      await page.screenshot({ path: `${OUTDIR}/14_risk_matrix.png`,
        clip: { x: 0, y: Math.max(0, box.y - 20), width: 1440, height: 400 } });
      console.log('✅ 14_risk_matrix');
    }
  }

  // ========== Silo A ==========
  await page.goto(`${BASE}/silo-a`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);
  await page.screenshot({ path: `${OUTDIR}/15_silo_a_full.png`, fullPage: true });
  console.log('✅ 15_silo_a_full');

  // Silo A - NIM API table
  const nimEl = page.locator('text=NIM API').first();
  if (await nimEl.count()) {
    await nimEl.scrollIntoViewIfNeeded();
    await page.waitForTimeout(300);
    const box = await nimEl.boundingBox();
    if (box) {
      await page.screenshot({ path: `${OUTDIR}/16_nim_api_services.png`,
        clip: { x: 0, y: Math.max(0, box.y - 20), width: 1440, height: 350 } });
      console.log('✅ 16_nim_api_services');
    }
  }

  // ========== Settings ==========
  await page.goto(`${BASE}/settings`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1000);
  await page.screenshot({ path: `${OUTDIR}/17_settings.png`, fullPage: true });
  console.log('✅ 17_settings');

  // ========== About ==========
  await page.goto(`${BASE}/about`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1000);
  await page.screenshot({ path: `${OUTDIR}/18_about.png`, fullPage: true });
  console.log('✅ 18_about');

  await browser.close();
  console.log('\n🎯 All captures complete');
}

main().catch(e => { console.error(e); process.exit(1); });
