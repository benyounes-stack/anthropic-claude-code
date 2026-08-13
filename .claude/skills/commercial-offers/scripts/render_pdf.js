#!/usr/bin/env node
/**
 * Render an HTML report to a print-ready PDF using headless Chromium (Playwright).
 *
 * Usage:
 *   node render_pdf.js <input.html> <output.pdf> [--brand path/to/brand.json]
 *
 * Reads company_name / footer_text from brand.json (defaults to the skill's
 * references/brand.json) so the footer and page numbers stay consistent across
 * reports without the HTML itself needing to hand-roll a repeating footer.
 */

const path = require('path');
const fs = require('fs');
const { pathToFileURL } = require('url');

function resolvePlaywright() {
  try {
    return require('playwright');
  } catch (_) {
    const globalRoot = require('child_process')
      .execSync('npm root -g')
      .toString()
      .trim();
    return require(path.join(globalRoot, 'playwright'));
  }
}

async function main() {
  const args = process.argv.slice(2);
  if (args.length < 2) {
    console.error('Usage: node render_pdf.js <input.html> <output.pdf> [--brand path/to/brand.json]');
    process.exit(1);
  }
  const [inputHtml, outputPdf] = args;
  const brandFlagIndex = args.indexOf('--brand');
  const brandPath = brandFlagIndex !== -1
    ? args[brandFlagIndex + 1]
    : path.join(__dirname, '..', 'references', 'brand.json');

  const brand = fs.existsSync(brandPath)
    ? JSON.parse(fs.readFileSync(brandPath, 'utf8'))
    : { company_name: '', footer_text: '' };

  const { chromium } = resolvePlaywright();
  const browser = await chromium.launch();
  const page = await browser.newPage();

  const fileUrl = pathToFileURL(path.resolve(inputHtml)).toString();
  await page.goto(fileUrl, { waitUntil: 'networkidle' });

  const footerLeft = brand.company_name || '';
  const footerRight = brand.footer_text || '';

  await page.pdf({
    path: path.resolve(outputPdf),
    format: 'A4',
    printBackground: true,
    margin: { top: '20mm', bottom: '18mm', left: '16mm', right: '16mm' },
    displayHeaderFooter: true,
    headerTemplate: '<span></span>',
    footerTemplate: `
      <div style="width:100%; font-size:8px; color:#6B7280; display:flex; justify-content:space-between; padding:0 16mm; font-family: Arial, sans-serif;">
        <span>${footerLeft}${footerLeft && footerRight ? ' — ' : ''}${footerRight}</span>
        <span>Page <span class="pageNumber"></span> / <span class="totalPages"></span></span>
      </div>`,
  });

  await browser.close();
  console.log(`PDF written to ${path.resolve(outputPdf)}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
