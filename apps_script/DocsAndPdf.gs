/**
 * Life Time Library – The Daily Edge
 * Google Docs & Free PDF Export Manager
 */

function getOrCreateFolder_(name, parentFolder) {
  const parent = parentFolder || DriveApp.getRootFolder();
  const it = parent.getFoldersByName(name);
  if (it.hasNext()) return it.next();
  return parent.createFolder(name);
}

function getLibraryFolders_() {
  const root = getOrCreateFolder_('LifeTimeLibrary', null);
  return {
    root: root,
    daily: getOrCreateFolder_('Daily Reports', root),
    pdf: getOrCreateFolder_('PDF Reports', root),
    weekly: getOrCreateFolder_('Weekly Reviews', root),
    monthly: getOrCreateFolder_('Monthly Reviews', root)
  };
}

function createGoogleDocAndPdfReport(title, bodyText, targetFolderType, exportPdf) {
  const folders = getLibraryFolders_();
  const targetFolder = folders[targetFolderType || 'daily'] || folders.daily;

  const doc = DocumentApp.create(title);
  const body = doc.getBody();
  body.appendParagraph('Life Time Library – The Daily Edge').setHeading(DocumentApp.ParagraphHeading.HEADING2);
  body.appendParagraph(title).setHeading(DocumentApp.ParagraphHeading.HEADING1);
  body.appendParagraph(bodyText);
  body.appendHorizontalRule();
  body.appendParagraph('Created by Hitesh Rawal | Life Time Library – The Daily Edge');
  body.appendParagraph('Connect with me on LinkedIn: https://www.linkedin.com/in/rawalhitesh/')
    .setLinkUrl('https://www.linkedin.com/in/rawalhitesh/');
  doc.saveAndClose();

  const docFile = DriveApp.getFileById(doc.getId());
  docFile.moveTo(targetFolder);

  let pdfUrl = '';
  if (exportPdf !== false) {
    const pdfBlob = docFile.getAs('application/pdf').setName(title + '.pdf');
    const pdfFile = folders.pdf.createFile(pdfBlob);
    pdfUrl = pdfFile.getUrl();
  }

  return {
    doc_url: docFile.getUrl(),
    pdf_url: pdfUrl,
    doc_id: doc.getId()
  };
}

function formatBriefForGoogleDoc_(brief) {
  const badge = String(brief.is_ai_verified).toUpperCase() === 'TRUE'
    ? 'Editorially Verified'
    : 'Curated Source Digest';

  return [
    '10 Minutes. Learn Daily. Live Intentionally. Evolve Continuously.',
    'Date: ' + brief.date + ' | Status: ' + badge + ' | Language: ' + (brief.language || 'Hinglish'),
    '',
    '1. HEALTH LESSON',
    cleanProse_(brief.health_lesson),
    '',
    '2. WEALTH LESSON (EDUCATIONAL ONLY)',
    cleanProse_(brief.wealth_lesson),
    '',
    '3. WISDOM LESSON',
    cleanProse_(brief.wisdom_lesson),
    '',
    '4. DEEP DIVE',
    cleanProse_(brief.deep_dive),
    '',
    '5. SURPRISING DISCOVERY',
    cleanProse_(brief.surprising_discovery),
    '',
    '6. MENTAL MODEL OF THE DAY',
    cleanProse_(brief.mental_model),
    '',
    "7. TODAY'S ACTION",
    cleanProse_(brief.todays_action),
    '',
    '8. REFLECTION QUESTION',
    cleanProse_(brief.reflection_question),
    '',
    '9. ORIGINAL SOURCES',
    brief.source_links
  ].join('\n');
}
