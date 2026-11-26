/**
 * LifeTimeLibrary – Optional Zero-Cloud-Console Web App Sync Bridge
 * Deploy as Web App (Execute as: Me) and set Script Property SHARED_SECRET.
 */

function doPost(e) {
  try {
    const payload = JSON.parse(e.postData.contents);
    const expectedSecret = PropertiesService.getScriptProperties().getProperty('SHARED_SECRET') || '';
    if (!expectedSecret || payload.secret !== expectedSecret) {
      return ContentService.createTextOutput(JSON.stringify({ status: 'unauthorized' }))
        .setMimeType(ContentService.MimeType.JSON);
    }

    const ss = getOrCreateSpreadsheet_();
    if (payload.action === 'create_doc_and_pdf') {
      const res = createGoogleDocAndPdfReport(payload.title, payload.body, 'daily', true);
      return ContentService.createTextOutput(JSON.stringify(Object.assign({ status: 'ok' }, res)))
        .setMimeType(ContentService.MimeType.JSON);
    }

    if (payload.action === 'sync_payload' && payload.tabs) {
      const synced = {};
      Object.keys(payload.tabs).forEach(tabName => {
        if (TAB_SCHEMAS[tabName]) {
          const uniqueMap = {
            Daily_Learning: 'date',
            Health_Research: 'original_article_link',
            Wealth_Research: 'original_article_link',
            Wisdom_Research: 'original_article_link',
            Sources: 'source_url',
            Weekly_Reviews: 'week_ending',
            Monthly_Reviews: 'month',
            Settings: 'key'
          };
          synced[tabName] = appendUniqueRows_(ss, tabName, payload.tabs[tabName], uniqueMap[tabName] || '');
        }
      });

      let emailResult = 'not_requested';
      if (payload.send_email && payload.tabs.Daily_Learning && payload.tabs.Daily_Learning.length > 0) {
        const latestBrief = payload.tabs.Daily_Learning[0];
        emailResult = sendDailyNewsletterEmail(ss, latestBrief, latestBrief.doc_url || '');
      }

      return ContentService.createTextOutput(JSON.stringify({ status: 'ok', synced: synced, email: emailResult }))
        .setMimeType(ContentService.MimeType.JSON);
    }

    return ContentService.createTextOutput(JSON.stringify({ status: 'unknown_action' }))
      .setMimeType(ContentService.MimeType.JSON);
  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({ status: 'error', message: err.message }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}
