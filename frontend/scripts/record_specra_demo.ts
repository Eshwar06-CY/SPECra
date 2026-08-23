import { chromium } from 'playwright';
import * as path from 'path';
import * as fs from 'fs';
import { execSync } from 'child_process';

const FFMPEG_PATH = 'C:\\Users\\meshw\\AppData\\Local\\Microsoft\\WinGet\\Packages\\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\\ffmpeg-9.0-full_build\\bin\\ffmpeg.exe';
const FFPROBE_PATH = 'C:\\Users\\meshw\\AppData\\Local\\Microsoft\\WinGet\\Packages\\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\\ffmpeg-9.0-full_build\\bin\\ffprobe.exe';

const SUBMISSION_DIR = 'D:\\Antigravity_Projects\\deadlock\\submission';
const RECORDINGS_TEMP_DIR = path.join(SUBMISSION_DIR, 'raw_recordings');

if (!fs.existsSync(SUBMISSION_DIR)) {
  fs.mkdirSync(SUBMISSION_DIR, { recursive: true });
}
if (!fs.existsSync(RECORDINGS_TEMP_DIR)) {
  fs.mkdirSync(RECORDINGS_TEMP_DIR, { recursive: true });
}

async function recordSPECraDemo() {
  console.log('--- Starting SPECra Demo Automation & Video Capture ---');

  const browser = await chromium.launch({
    headless: false,
    args: [
      '--start-maximized',
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--window-size=1920,1080',
    ],
  });

  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 },
    recordVideo: {
      dir: RECORDINGS_TEMP_DIR,
      size: { width: 1920, height: 1080 },
    },
  });

  const page = await context.newPage();

  // Helper for smooth pause
  const pause = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

  try {
    // ----------------------------------------------------
    // SCENE A: LANDING PAGE
    // ----------------------------------------------------
    console.log('Scene A: Landing Page...');
    await page.goto('http://localhost:5173/#/landing', { waitUntil: 'networkidle' });
    await pause(3000);

    // Smooth scroll down to highlight value proposition
    await page.evaluate(() => window.scrollBy({ top: 550, behavior: 'smooth' }));
    await pause(3500);

    await page.evaluate(() => window.scrollBy({ top: 750, behavior: 'smooth' }));
    await pause(3500);

    // Scroll back up to Hero CTA
    await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' }));
    await pause(2500);

    // Click Sign In or Explore
    console.log('Scene B: Login & Authentication...');
    const signInBtn = page.locator('button:has-text("Sign in")').first();
    if (await signInBtn.isVisible()) {
      await signInBtn.click();
    } else {
      await page.goto('http://localhost:5173/#/login');
    }
    await pause(3000);

    // Click Sign In on the Login Form
    const submitBtn = page.locator('button[type="submit"]:has-text("Sign in")').first();
    if (await submitBtn.isVisible()) {
      await submitBtn.click();
    }
    await pause(3500);

    // ----------------------------------------------------
    // SCENE C: DASHBOARD
    // ----------------------------------------------------
    console.log('Scene C: Personalized Enterprise Dashboard...');
    await page.goto('http://localhost:5173/#/dashboard', { waitUntil: 'networkidle' });
    await pause(4500);

    // Scroll slightly to show catalog statistics and recent activity
    await page.evaluate(() => window.scrollBy({ top: 350, behavior: 'smooth' }));
    await pause(3500);
    await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' }));
    await pause(2000);

    // ----------------------------------------------------
    // SCENE D: NEW ANALYSIS / UPLOAD
    // ----------------------------------------------------
    console.log('Scene D: Catalog Ingestion & Schema Detection...');
    await page.goto('http://localhost:5173/#/upload', { waitUntil: 'networkidle' });
    await pause(3500);

    // If an example catalog button or upload area exists, show understanding
    await page.goto('http://localhost:5173/#/understand', { waitUntil: 'networkidle' });
    await pause(4000);

    // ----------------------------------------------------
    // SCENE E: DEFINE REQUIREMENTS
    // ----------------------------------------------------
    console.log('Scene E: Natural Language Requirements...');
    await page.goto('http://localhost:5173/#/requirements', { waitUntil: 'networkidle' });
    await pause(2500);

    // Type the requirement in natural language
    const textarea = page.locator('textarea').first();
    if (await textarea.isVisible()) {
      await textarea.fill('');
      await textarea.pressSequentially(
        'Find abrasive products and extract manufacturer, brand, manufacturer part number, dimensions and packaging information.',
        { delay: 35 }
      );
      await pause(2500);
    }

    // ----------------------------------------------------
    // SCENE F: RESULTS & PRODUCT INTELLIGENCE & EVIDENCE
    // ----------------------------------------------------
    console.log('Scene F: Results, Product Intelligence & Traceable Evidence...');
    // Seed AppContext state with successfully enriched product
    await page.evaluate(() => {
      localStorage.setItem('specra_selected_job', '327d0ad0-d356-43d6-8d6d-a6f86da4c46f');
      localStorage.setItem('specra_selected_product', 'b17feefb-5796-4b91-b487-dd6eb9bad9f7');
      localStorage.setItem('specra_active_query', 'Find abrasive products and extract manufacturer, brand, dimensions and packaging');
    });

    await page.goto('http://localhost:5173/#/results', { waitUntil: 'networkidle' });
    await pause(5000);

    // Click on Inspect Product / View Evidence if available
    const inspectBtn = page.locator('button:has-text("Inspect product"), button:has-text("View Evidence"), button:has-text("Inspect")').first();
    if (await inspectBtn.isVisible()) {
      await inspectBtn.click();
      await pause(4500);

      // Scroll inside drawer if open
      const drawer = page.locator('aside, .specra-drawer, div[role="dialog"]').first();
      if (await drawer.isVisible()) {
        await drawer.evaluate((el) => el.scrollBy({ top: 300, behavior: 'smooth' }));
        await pause(3500);
        await drawer.evaluate((el) => el.scrollTo({ top: 0, behavior: 'smooth' }));
        await pause(2000);
      }
    }

    // ----------------------------------------------------
    // SCENE G: DATA QUALITY & VALIDATION AUDIT
    // ----------------------------------------------------
    console.log('Scene G: Data Quality & Physical Consistency Audit...');
    await page.goto('http://localhost:5173/#/validation', { waitUntil: 'networkidle' });
    await pause(5000);

    await page.evaluate(() => window.scrollBy({ top: 300, behavior: 'smooth' }));
    await pause(3500);
    await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' }));
    await pause(2000);

    // ----------------------------------------------------
    // SCENE H: EXPORT (252-COLUMN UNIHACK & CUSTOM DATASET)
    // ----------------------------------------------------
    console.log('Scene H: 252-Column Enterprise Export...');
    await page.goto('http://localhost:5173/#/export', { waitUntil: 'networkidle' });
    await pause(5000);

    await page.evaluate(() => window.scrollBy({ top: 300, behavior: 'smooth' }));
    await pause(3500);

    // ----------------------------------------------------
    // SCENE I: CLOSING & CREDITS
    // ----------------------------------------------------
    console.log('Scene I: Closing & Credits Screen...');
    await page.evaluate(() => {
      document.body.innerHTML = `
        <div style="min-height: 100vh; background: #07090e; color: #f8fafc; font-family: system-ui, -apple-system, sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; padding: 40px; position: relative; overflow: hidden;">
          <div style="position: absolute; width: 800px; height: 500px; background: radial-gradient(circle, rgba(6,182,212,0.18) 0%, rgba(59,130,246,0.08) 50%, transparent 70%); filter: blur(90px); pointer-events: none;"></div>
          
          <div style="display: flex; align-items: center; gap: 18px; margin-bottom: 24px; z-index: 10;">
            <svg width="56" height="56" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
              <defs>
                <linearGradient id="g1" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stop-color="#06b6d4" />
                  <stop offset="100%" stop-color="#3b82f6" />
                </linearGradient>
              </defs>
              <rect x="4" y="4" width="32" height="32" rx="9" fill="#0f172a" stroke="url(#g1)" stroke-width="2" />
              <path d="M12 13h16c1.1 0 2 .9 2 2v2H12v-4z" fill="url(#g1)" />
              <path d="M12 21h16c1.1 0 2 .9 2 2v2H12v-4z" fill="url(#g1)" opacity="0.8" />
              <circle cx="15" cy="15" r="1.5" fill="#ffffff" />
              <circle cx="21" cy="23" r="1.5" fill="#ffffff" />
            </svg>
            <span style="font-size: 52px; font-weight: 900; letter-spacing: -0.04em; background: linear-gradient(135deg, #ffffff 30%, #38bdf8 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">SPECra</span>
          </div>

          <p style="font-size: 24px; font-weight: 600; color: #94a3b8; max-width: 720px; line-height: 1.5; margin-bottom: 48px; z-index: 10;">
            Turn messy industrial product data into trusted, validated commerce intelligence.
          </p>

          <div style="background: rgba(15, 23, 42, 0.7); backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 24px; padding: 36px 64px; display: flex; flex-direction: column; gap: 16px; z-index: 10; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);">
            <div style="font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.15em; color: #38bdf8; margin-bottom: 4px;">Created & Presented by</div>
            <div style="font-size: 28px; font-weight: 800; color: #ffffff; letter-spacing: -0.02em;">Eshwar M &nbsp;•&nbsp; Granthini CA</div>
            <div style="font-size: 17px; font-weight: 500; color: #cbd5e1;">Vidyavardhaka College of Engineering</div>
            <div style="margin-top: 12px; font-size: 14px; font-weight: 600; color: #64748b; letter-spacing: 0.05em; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 16px;">
              Team <span style="color: #38bdf8; font-weight: 700;">DEADLOCK</span> • UniHack 2026
            </div>
          </div>
        </div>
      `;
    });
    await pause(6500);

    console.log('User Journey recording completed successfully.');
  } catch (err) {
    console.error('Error during recording execution:', err);
  } finally {
    const videoPage = page.video();
    await page.close();
    await context.close();
    await browser.close();

    if (videoPage) {
      const rawVideoPath = await videoPage.path();
      console.log(`Raw video saved to: ${rawVideoPath}`);

      const fullOutputMp4 = path.join(SUBMISSION_DIR, 'specra_demo.mp4');
      const shortOutputMp4 = path.join(SUBMISSION_DIR, 'specra_short_demo.mp4');

      console.log('Encoding Full Demo MP4 (specra_demo.mp4)...');
      execSync(
        `"${FFMPEG_PATH}" -y -i "${rawVideoPath}" -c:v libx264 -preset slow -crf 20 -pix_fmt yuv420p -r 30 "${fullOutputMp4}"`,
        { stdio: 'inherit' }
      );

      console.log('Encoding Short Demo MP4 (specra_short_demo.mp4)...');
      // Create high-paced short demo by trimming or speeding up
      execSync(
        `"${FFMPEG_PATH}" -y -i "${fullOutputMp4}" -filter:v "setpts=0.55*PTS" -an -r 30 "${shortOutputMp4}"`,
        { stdio: 'inherit' }
      );

      console.log('Verifying Generated MP4 Video Files...');
      const fullProbe = execSync(
        `"${FFPROBE_PATH}" -v error -show_entries format=duration,size,bit_rate:stream=width,height,codec_name,r_frame_rate -of default=noprint_wrappers=1 "${fullOutputMp4}"`
      ).toString();
      console.log('--- specra_demo.mp4 Metadata ---');
      console.log(fullProbe);

      const shortProbe = execSync(
        `"${FFPROBE_PATH}" -v error -show_entries format=duration,size,bit_rate:stream=width,height,codec_name,r_frame_rate -of default=noprint_wrappers=1 "${shortOutputMp4}"`
      ).toString();
      console.log('--- specra_short_demo.mp4 Metadata ---');
      console.log(shortProbe);
    }
  }
}

recordSPECraDemo().catch(console.error);
