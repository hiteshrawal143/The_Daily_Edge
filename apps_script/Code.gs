/**
 * LifeTimeLibrary – Main Entry Points & Spreadsheet Menu
 */

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('LifeTimeLibrary')
    .addItem('1. Initialize 12 Database Tabs', 'setupLifeTimeLibrary')
    .addItem('2. Run Daily RSS Digest Now', 'runDailyRssFallbackPipeline')
    .addItem('3. Run Weekly Review Now', 'runWeeklyReviewInAppsScript')
    .addItem('4. Install 7 AM IST Daily Trigger', 'installDailyAndWeeklyTriggers')
    .addToUi();
}

function setupLifeTimeLibrary() {
  const url = initializeDatabaseTabs();
  getLibraryFolders_();
  Logger.log('LifeTimeLibrary Knowledge Database ready: ' + url);
  return url;
}

function runDailyRssFallbackPipeline() {
  const startMs = Date.now();
  const ss = getOrCreateSpreadsheet_();
  initializeDatabaseTabs();

  const collected = collectAllRssInAppsScript(ss);
  const todayStr = Utilities.formatDate(new Date(), 'Asia/Kolkata', 'yyyy-MM-dd');

  const pickTop = (arr) => arr.slice(0, 2).map((a, i) =>
    (i + 1) + '. ' + a.article_title + ' (' + a.source_name + ')\n' + a.summary + '\nLink: ' + a.original_article_link
  ).join('\n\n') || '[RSS-Only Digest – Not AI-Verified] No new items collected today.';

  const links = []
    .concat(collected.Health.slice(0, 2), collected.Wealth.slice(0, 2), collected.Wisdom.slice(0, 2))
    .map(a => a.original_article_link)
    .join('\n');

  const brief = {
    date: todayStr,
    title: 'The Daily Edge – Health, Wealth & Wisdom – ' + todayStr,
    language: 'Hinglish',
    is_ai_verified: 'FALSE',
    health_lesson: pickTop(collected.Health),
    wealth_lesson: pickTop(collected.Wealth),
    wisdom_lesson: pickTop(collected.Wisdom),
    deep_dive: 'Read the top linked research article in full today and note what is direct evidence versus interpretation.',
    surprising_discovery: 'Explore today\'s newly archived insights inside your Life Time Library dashboard.',
    mental_model: 'First-Principles Verification: Separate facts, expert opinions, and speculation.',
    todays_action: 'Read 1 original research link and save 1 takeaway in Bookmarks.',
    reflection_question: 'Which insight today challenged an assumption I previously held?',
    source_links: links,
    doc_url: '',
    pdf_url: '',
    email_status: 'pending',
    created_at: new Date().toISOString()
  };

  const docTitle = 'Daily_Growth_Brief_' + todayStr.replace(/-/g, '_');
  const exportPdf = getSettingValue_(ss, 'EXPORT_PDF', 'TRUE').toUpperCase() === 'TRUE';
  const docRes = createGoogleDocAndPdfReport(docTitle, formatBriefForGoogleDoc_(brief), 'daily', exportPdf);
  brief.doc_url = docRes.doc_url;
  brief.pdf_url = docRes.pdf_url;
  brief.email_status = sendDailyNewsletterEmail(ss, brief, docRes.doc_url);

  appendUniqueRows_(ss, 'Daily_Learning', [brief], 'date');
  const dur = ((Date.now() - startMs) / 1000).toFixed(2);
  logAutomationRun_(ss, 'daily_apps_script_fallback', 'success', 'rss_only_fallback_not_ai_verified', docRes.doc_url, dur);
}
