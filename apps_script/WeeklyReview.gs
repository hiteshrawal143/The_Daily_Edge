/**
 * LifeTimeLibrary – Sunday Weekly Learning Review Generator
 */

function runWeeklyReviewInAppsScript() {
  const ss = getOrCreateSpreadsheet_();
  const weekEnding = Utilities.formatDate(new Date(), 'Asia/Kolkata', 'yyyy-MM-dd');

  const healthSheet = ss.getSheetByName('Health_Research');
  const wealthSheet = ss.getSheetByName('Wealth_Research');
  const wisdomSheet = ss.getSheetByName('Wisdom_Research');

  const hCount = Math.max(0, healthSheet.getLastRow() - 1);
  const wCount = Math.max(0, wealthSheet.getLastRow() - 1);
  const wiCount = Math.max(0, wisdomSheet.getLastRow() - 1);

  const summary = 'Week ending ' + weekEnding + ': Health=' + hCount + ', Wealth=' + wCount + ', Wisdom=' + wiCount + ' total archived items.';
  const docTitle = 'Weekly_Learning_Review_' + weekEnding.replace(/-/g, '_');
  const docRes = createGoogleDocAndPdfReport(docTitle, summary + '\n\nReview your top lessons and complete the weekly quiz in the Streamlit dashboard.', 'weekly', true);

  appendUniqueRows_(ss, 'Weekly_Reviews', [{
    week_ending: weekEnding,
    summary: summary,
    top_10_learnings: 'See Health/Wealth/Wisdom tabs for top ranked entries.',
    health_progress: hCount + ' archived items',
    wealth_progress: wCount + ' archived items',
    wisdom_progress: wiCount + ' archived items',
    revision_topics: 'Revise low-score quiz topics and Bookmarks.',
    next_week_suggestions: 'Maintain daily 10-minute reading + 1 weekly reflection.',
    doc_url: docRes.doc_url,
    created_at: new Date().toISOString()
  }], 'week_ending');

  logAutomationRun_(ss, 'weekly_review_apps_script', 'success', 'apps_script_summary', docRes.doc_url, 1);
}
