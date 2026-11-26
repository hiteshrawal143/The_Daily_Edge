/**
 * LifeTimeLibrary – Time-Driven Triggers (7:00 AM IST Daily & Sunday Weekly)
 */

function installDailyAndWeeklyTriggers() {
  // Remove existing triggers for these handlers to prevent duplicates
  const existing = ScriptApp.getProjectTriggers();
  existing.forEach(t => {
    const fn = t.getHandlerFunction();
    if (fn === 'runDailyRssFallbackPipeline' || fn === 'runWeeklyReviewInAppsScript') {
      ScriptApp.deleteTrigger(t);
    }
  });

  // Daily 7:00 AM Asia/Kolkata
  ScriptApp.newTrigger('runDailyRssFallbackPipeline')
    .timeBased()
    .everyDays(1)
    .atHour(7)
    .inTimezone('Asia/Kolkata')
    .create();

  // Sunday 8:00 AM Asia/Kolkata
  ScriptApp.newTrigger('runWeeklyReviewInAppsScript')
    .timeBased()
    .onWeekDay(ScriptApp.WeekDay.SUNDAY)
    .atHour(8)
    .inTimezone('Asia/Kolkata')
    .create();

  Logger.log('Installed 7:00 AM IST daily trigger and Sunday 8:00 AM IST weekly trigger.');
}
