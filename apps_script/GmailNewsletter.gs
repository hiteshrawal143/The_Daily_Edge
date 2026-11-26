/**
 * Life Time Library – The Daily Edge
 * Free Gmail Newsletter Delivery (MailApp) with Creator Attribution & Safe Citations
 * Strictly enforces recipient configuration and explicit user authorization before sending.
 */

const CREATOR_NAME = 'Hitesh Rawal';
const CREATOR_LINKEDIN_URL = 'https://www.linkedin.com/in/rawalhitesh/';

function sendDailyNewsletterEmail(ss, brief, docUrl) {
  const recipient = getSettingValue_(ss, 'RECIPIENT_EMAIL', '');
  const approved = getSettingValue_(ss, 'EMAIL_APPROVED', 'FALSE').toUpperCase() === 'TRUE';

  if (!recipient || !approved) {
    Logger.log('Email skipped: configure RECIPIENT_EMAIL and set EMAIL_APPROVED=TRUE in Settings tab first.');
    return 'blocked_pending_recipient_approval';
  }

  const remainingQuota = MailApp.getRemainingDailyQuota();
  if (remainingQuota < 1) {
    Logger.log('Gmail free daily quota exhausted for today.');
    return 'skipped_quota_exhausted';
  }

  const subject = 'The Daily Edge – Health, Wealth & Wisdom – ' + brief.date;
  const htmlBody = buildNewsletterHtml_(brief, docUrl);

  MailApp.sendEmail({
    to: recipient,
    subject: subject,
    htmlBody: htmlBody,
    name: 'Life Time Library – The Daily Edge'
  });

  return 'sent_via_mailapp (quota remaining: ' + (remainingQuota - 1) + ')';
}

function escapeHtml_(s) {
  return String(s || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\n/g, '<br>');
}

function cleanProse_(s) {
  return String(s || '')
    .replace(/\[RSS-Only Digest[^\]]*\]\s*/gi, '')
    .replace(/Classification:\s*[a-z_]+/gi, '')
    .replace(/https?:\/\/\S+/g, '')
    .trim();
}

function renderSourceListHtml_(rawLinks) {
  const urls = String(rawLinks || '').split(/\r?\n/).map(u => u.trim()).filter(Boolean);
  if (urls.length === 0) return '<li>Sources archived in Life Time Library.</li>';
  return urls.map(url => {
    const hostMatch = url.match(/^https?:\/\/(?:www\.)?([^\/]+)/i);
    const label = hostMatch ? hostMatch[1] : 'Research Source';
    return '<li style="margin-bottom:6px;"><strong>Source: ' + escapeHtml_(label) + '</strong> &ndash; <a href="' + url + '" target="_blank" rel="noopener noreferrer" style="color:#1D4ED8;text-decoration:none;font-weight:bold;">Read Original Research &#8599;</a></li>';
  }).join('\n');
}

function buildNewsletterHtml_(brief, docUrl) {
  const isAi = String(brief.is_ai_verified).toUpperCase() === 'TRUE';
  const badgeBg = isAi ? '#14532D' : '#334155';
  const badgeText = isAi ? 'Editorially Verified' : 'Curated Source Digest';
  const docHtml = docUrl
    ? '<p style="margin-top:12px;"><a href="' + docUrl + '" target="_blank" rel="noopener noreferrer" style="background:#C59B38;color:#0B162C;padding:9px 16px;border-radius:6px;text-decoration:none;font-weight:bold;font-size:13px;">Open Google Docs Report &#8599;</a></p>'
    : '';

  return [
    '<div style="font-family:Segoe UI,Arial,sans-serif;max-width:660px;margin:auto;background:#FFFFFF;border:1px solid #E5E0D5;border-radius:14px;overflow:hidden;">',
    '  <div style="background:#0B162C;color:#FAF8F3;padding:24px 28px;border-bottom:3px solid #C59B38;">',
    '    <div style="font-size:11px;letter-spacing:1.6px;color:#C59B38;font-weight:bold;">LIFE TIME LIBRARY</div>',
    '    <h2 style="margin:6px 0 4px 0;font-family:Georgia,serif;color:#FFFFFF;">The Daily Edge</h2>',
    '    <div style="font-size:12.5px;color:#CBD5E1;margin-bottom:10px;">10 Minutes. Learn Daily. Live Intentionally. Evolve Continuously.</div>',
    '    <span style="background:' + badgeBg + ';color:#fff;padding:4px 10px;border-radius:12px;font-size:11px;">' + escapeHtml_(brief.date) + ' &bull; ' + badgeText + '</span>',
    docHtml,
    '  </div>',
    '  <div style="padding:24px 28px;color:#0F172A;line-height:1.65;">',
    '    <h3 style="color:#1F7A5C;">1. Health Lesson</h3><p>' + escapeHtml_(cleanProse_(brief.health_lesson)) + '</p>',
    '    <h3 style="color:#1D4ED8;">2. Wealth Lesson (Educational Only)</h3><p>' + escapeHtml_(cleanProse_(brief.wealth_lesson)) + '</p>',
    '    <h3 style="color:#6D28D9;">3. Wisdom Lesson</h3><p>' + escapeHtml_(cleanProse_(brief.wisdom_lesson)) + '</p>',
    '    <h3>Deep Dive</h3><p>' + escapeHtml_(cleanProse_(brief.deep_dive)) + '</p>',
    '    <h3>Surprising Discovery</h3><p>' + escapeHtml_(cleanProse_(brief.surprising_discovery)) + '</p>',
    '    <h3>Mental Model of the Day</h3><p>' + escapeHtml_(cleanProse_(brief.mental_model)) + '</p>',
    '    <h3>Today\'s Action</h3><p>' + escapeHtml_(cleanProse_(brief.todays_action)) + '</p>',
    '    <h3>Reflection Question</h3><p>' + escapeHtml_(cleanProse_(brief.reflection_question)) + '</p>',
    '    <h3>Original Sources</h3><ul>' + renderSourceListHtml_(brief.source_links) + '</ul>',
    '  </div>',
    '  <div style="background:#0B162C;color:#CBD5E1;padding:18px 28px;border-top:2px solid #C59B38;text-align:center;font-size:12px;">',
    '    <div style="color:#FFFFFF;font-weight:bold;">Created by ' + CREATOR_NAME + ' | Life Time Library – The Daily Edge</div>',
    '    <div style="margin:8px 0;"><a href="' + CREATOR_LINKEDIN_URL + '" target="_blank" rel="noopener noreferrer" style="color:#60A5FA;text-decoration:none;font-weight:bold;">Connect with me on LinkedIn &#8599;</a></div>',
    '    <div style="color:#94A3B8;font-size:11px;">&copy; 2026 ' + CREATOR_NAME + '. All rights reserved. Built to learn. Designed to grow. Created for life.</div>',
    '  </div>',
    '</div>'
  ].join('\n');
}
