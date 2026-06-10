import { chromium } from 'playwright';

const OUTDIR = '/Users/gimdongju/Documents/workspace/secu/PRST_N_FM/docs/screenshots';
const BASE = 'http://localhost:5173';

async function main() {
  const browser = await chromium.launch();
  const ctx = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 2,
  });
  const page = await ctx.newPage();

  // 1. Silo B 전체 페이지
  await page.goto(`${BASE}/silo-b`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);
  await page.screenshot({ path: `${OUTDIR}/01_silo_b_full.png`, fullPage: true });
  console.log('✅ 01_silo_b_full');

  // 2. ExperimentControl (상단)
  const expCtrl = page.locator('section, div').filter({ hasText: /Iterations|Start Experiment/i }).first();
  if (await expCtrl.count()) {
    await expCtrl.screenshot({ path: `${OUTDIR}/02_experiment_control.png` });
    console.log('✅ 02_experiment_control');
  } else {
    await page.screenshot({ path: `${OUTDIR}/02_experiment_control.png`, clip: { x: 0, y: 0, width: 1440, height: 500 } });
    console.log('✅ 02_experiment_control (clip)');
  }

  // 3. CandidateTable 영역
  const table = page.locator('table').first();
  if (await table.count()) {
    await table.screenshot({ path: `${OUTDIR}/03_candidate_table.png` });
    console.log('✅ 03_candidate_table');
  }

  // 4. 스크롤하면서 각 컴포넌트 캡처
  const sections = [
    { name: '04_convergence', text: /Best ddG|Convergence/i },
    { name: '05_ddg_distribution', text: /Distribution|Histogram/i },
    { name: '06_sar_heatmap', text: /SAR|Heatmap|Structure-Activity/i },
    { name: '07_sequence_logo', text: /Sequence Logo|Information/i },
    { name: '08_mutation_analysis', text: /Mutation Analysis|FWKT/i },
    { name: '09_pharmacology', text: /Pharmacology|GRAVY|Boman/i },
    { name: '10_validation', text: /Validation|PASS|CAUTION/i },
    { name: '11_qc_gate', text: /QC Gate|Pass Rate/i },
    { name: '12_risk_matrix', text: /Risk Matrix|Probability/i },
    { name: '13_run_comparison', text: /Run Comparison|History/i },
  ];

  for (const s of sections) {
    const el = page.locator('section, div, h2, h3').filter({ hasText: s.text }).first();
    if (await el.count()) {
      try {
        await el.scrollIntoViewIfNeeded();
        await page.waitForTimeout(500);
        // Get bounding box and capture parent section
        const box = await el.boundingBox();
        if (box) {
          const y = Math.max(0, box.y - 20);
          await page.screenshot({
            path: `${OUTDIR}/${s.name}.png`,
            clip: { x: 0, y, width: 1440, height: Math.min(800, 900) },
          });
          console.log(`✅ ${s.name}`);
        }
      } catch (e) {
        console.log(`⚠️ ${s.name}: ${e.message}`);
      }
    } else {
      console.log(`⏭️ ${s.name}: not found`);
    }
  }

  // 5. Silo A 페이지
  await page.goto(`${BASE}/silo-a`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);
  await page.screenshot({ path: `${OUTDIR}/14_silo_a_full.png`, fullPage: true });
  console.log('✅ 14_silo_a_full');

  // 6. About 페이지
  await page.goto(`${BASE}/about`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1000);
  await page.screenshot({ path: `${OUTDIR}/15_about.png`, fullPage: true });
  console.log('✅ 15_about');

  // 7. Settings 페이지
  await page.goto(`${BASE}/settings`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1000);
  await page.screenshot({ path: `${OUTDIR}/16_settings.png`, fullPage: true });
  console.log('✅ 16_settings');

  await browser.close();
  console.log('\n🎯 Screenshot capture complete');
}

main().catch(e => { console.error(e); process.exit(1); });
