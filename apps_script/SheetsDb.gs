/**
 * LifeTimeLibrary – Google Sheets Knowledge Database Manager
 * Creates "LifeTimeLibrary Knowledge Database" with all 12 tabs and deduplication helpers.
 */

const SPREADSHEET_NAME = 'LifeTimeLibrary Knowledge Database';

const TAB_SCHEMAS = {
  Daily_Learning: [
    'date', 'title', 'language', 'is_ai_verified', 'health_lesson', 'wealth_lesson',
    'wisdom_lesson', 'deep_dive', 'surprising_discovery', 'mental_model',
    'todays_action', 'reflection_question', 'source_links', 'doc_url', 'pdf_url',
    'email_status', 'created_at'
  ],
  Health_Research: [
    'article_id', 'source_name', 'source_url', 'publication_date', 'article_title',
    'category', 'original_article_link', 'date_collected', 'summary',
    'credibility_score', 'relevance_score', 'claim_classification', 'used_in_brief'
  ],
  Wealth_Research: [
    'article_id', 'source_name', 'source_url', 'publication_date', 'article_title',
    'category', 'original_article_link', 'date_collected', 'summary',
    'credibility_score', 'relevance_score', 'claim_classification', 'used_in_brief'
  ],
  Wisdom_Research: [
    'article_id', 'source_name', 'source_url', 'publication_date', 'article_title',
    'category', 'original_article_link', 'date_collected', 'summary',
    'credibility_score', 'relevance_score', 'claim_classification', 'used_in_brief'
  ],
  Sources: [
    'pillar', 'source_name', 'source_url', 'source_type', 'credibility_weight',
    'topics', 'active', 'last_checked', 'last_status'
  ],
  Topic_History: ['date', 'pillar', 'topic_slug', 'topic_title', 'article_link', 'brief_date'],
  Bookmarks: ['bookmark_id', 'date_saved', 'pillar', 'title', 'lesson_text', 'source_link', 'notes'],
  Quiz_Results: [
    'quiz_id', 'week_ending', 'question_no', 'pillar', 'question',
    'user_answer', 'correct_answer', 'is_correct', 'explanation', 'submitted_at'
  ],
  Weekly_Reviews: [
    'week_ending', 'summary', 'top_10_learnings', 'health_progress', 'wealth_progress',
    'wisdom_progress', 'revision_topics', 'next_week_suggestions', 'doc_url', 'created_at'
  ],
  Monthly_Reviews: [
    'month', 'summary', 'top_insights', 'pillar_breakdown', 'quiz_accuracy', 'doc_url', 'created_at'
  ],
  Automation_Logs: ['timestamp', 'workflow', 'status', 'ai_mode', 'details', 'duration_sec'],
  Settings: ['key', 'value', 'updated_at']
};

function getOrCreateSpreadsheet_() {
  const props = PropertiesService.getScriptProperties();
  const savedId = props.getProperty('SPREADSHEET_ID');
  if (savedId) {
    try {
      return SpreadsheetApp.openById(savedId);
    } catch (e) {
      Logger.log('Saved spreadsheet not accessible, searching Drive: ' + e);
    }
  }

  const files = DriveApp.getFilesByName(SPREADSHEET_NAME);
  if (files.hasNext()) {
    const ss = SpreadsheetApp.open(files.next());
    props.setProperty('SPREADSHEET_ID', ss.getId());
    return ss;
  }

  const ss = SpreadsheetApp.create(SPREADSHEET_NAME);
  props.setProperty('SPREADSHEET_ID', ss.getId());
  return ss;
}

function initializeDatabaseTabs() {
  const ss = getOrCreateSpreadsheet_();
  const existing = {};
  ss.getSheets().forEach(s => { existing[s.getName()] = s; });

  Object.keys(TAB_SCHEMAS).forEach(tabName => {
    const headers = TAB_SCHEMAS[tabName];
    let sheet = existing[tabName];
    if (!sheet) {
      sheet = ss.insertSheet(tabName);
    }
    if (sheet.getLastRow() === 0) {
      sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
      sheet.setFrozenRows(1);
      sheet.getRange(1, 1, 1, headers.length).setFontWeight('bold');
    }
  });

  // Remove default "Sheet1" if empty and unused
  const defaultSheet = ss.getSheetByName('Sheet1');
  if (defaultSheet && ss.getSheets().length > 1 && defaultSheet.getLastRow() === 0) {
    ss.deleteSheet(defaultSheet);
  }

  seedDefaultSettings_(ss);
  return ss.getUrl();
}

function seedDefaultSettings_(ss) {
  const sheet = ss.getSheetByName('Settings');
  const existingKeys = new Set();
  const lastRow = sheet.getLastRow();
  if (lastRow > 1) {
    sheet.getRange(2, 1, lastRow - 1, 1).getValues().forEach(r => existingKeys.add(String(r[0])));
  }
  const nowStr = new Date().toISOString();
  const defaults = [
    ['RECIPIENT_EMAIL', '', nowStr],
    ['EMAIL_APPROVED', 'FALSE', nowStr],
    ['TIMEZONE', 'Asia/Kolkata', nowStr],
    ['DAILY_HOUR_IST', '7', nowStr],
    ['BUDGET_INR', '0', nowStr],
    ['EXPORT_PDF', 'TRUE', nowStr]
  ];
  const toInsert = defaults.filter(row => !existingKeys.has(row[0]));
  if (toInsert.length > 0) {
    sheet.getRange(sheet.getLastRow() + 1, 1, toInsert.length, 3).setValues(toInsert);
  }
}

function getSettingValue_(ss, key, fallback) {
  const sheet = ss.getSheetByName('Settings');
  if (!sheet || sheet.getLastRow() < 2) return fallback;
  const rows = sheet.getRange(2, 1, sheet.getLastRow() - 1, 2).getValues();
  for (let i = 0; i < rows.length; i++) {
    if (String(rows[i][0]).trim() === key) {
      return String(rows[i][1]).trim();
    }
  }
  return fallback;
}

function appendUniqueRows_(ss, tabName, objects, uniqueKeyField) {
  const headers = TAB_SCHEMAS[tabName];
  const sheet = ss.getSheetByName(tabName);
  if (!sheet || !objects || objects.length === 0) return 0;

  const keyIdx = headers.indexOf(uniqueKeyField);
  const existingKeys = new Set();
  if (keyIdx >= 0 && sheet.getLastRow() > 1) {
    const colVals = sheet.getRange(2, keyIdx + 1, sheet.getLastRow() - 1, 1).getValues();
    colVals.forEach(r => {
      if (r[0]) existingKeys.add(String(r[0]).trim());
    });
  }

  const rowsToAppend = [];
  objects.forEach(obj => {
    const k = uniqueKeyField ? String(obj[uniqueKeyField] || '').trim() : '';
    if (!uniqueKeyField || (k && !existingKeys.has(k))) {
      if (k) existingKeys.add(k);
      rowsToAppend.push(headers.map(h => obj[h] !== undefined ? String(obj[h]) : ''));
    }
  });

  if (rowsToAppend.length > 0) {
    sheet.getRange(sheet.getLastRow() + 1, 1, rowsToAppend.length, headers.length).setValues(rowsToAppend);
  }
  return rowsToAppend.length;
}

function logAutomationRun_(ss, workflow, status, aiMode, details, durationSec) {
  const sheet = ss.getSheetByName('Automation_Logs');
  if (!sheet) return;
  sheet.appendRow([new Date().toISOString(), workflow, status, aiMode, details, String(durationSec || 0)]);
}
