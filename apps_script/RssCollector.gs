/**
 * LifeTimeLibrary – Free RSS/Atom Research Collector (Google Apps Script)
 * Uses built-in UrlFetchApp and XmlService. Zero paid scraping or API billing.
 */

const DEFAULT_RSS_SOURCES = {
  Health: [
    { name: 'Nature Neuroscience', url: 'https://www.nature.com/neuro.rss', type: 'scientific_feed', weight: 10 },
    { name: 'PLOS Medicine', url: 'https://journals.plos.org/plosmedicine/feed/atom', type: 'scientific_feed', weight: 10 },
    { name: 'Medical Xpress', url: 'https://medicalxpress.com/rss-feed/', type: 'scientific_feed', weight: 9 },
    { name: 'ScienceDaily Mind & Brain', url: 'https://www.sciencedaily.com/rss/mind_brain.xml', type: 'scientific_feed', weight: 9 },
    { name: 'ScienceDaily Health & Medicine', url: 'https://www.sciencedaily.com/rss/health_medicine.xml', type: 'scientific_feed', weight: 9 },
    { name: 'WHO News', url: 'https://www.who.int/rss-feeds/news-english.xml', type: 'official_public_health', weight: 10 }
  ],
  Wealth: [
    { name: 'RBI Press Releases', url: 'https://www.rbi.org.in/pressreleases_rss.xml', type: 'official_institution', weight: 10 },
    { name: 'Finshots', url: 'https://finshots.in/rss/', type: 'educational_blog', weight: 8 },
    { name: 'Of Dollars And Data', url: 'https://ofdollarsanddata.com/feed/', type: 'educational_blog', weight: 9 },
    { name: 'Y Combinator Blog', url: 'https://www.ycombinator.com/blog/rss/', type: 'startup_blog', weight: 9 },
    { name: 'FRED Economics Blog', url: 'https://fredblog.stlouisfed.org/feed/', type: 'economics_blog', weight: 9 },
    { name: 'Google AI Blog', url: 'https://blog.google/technology/ai/rss/', type: 'official_tech_blog', weight: 9 }
  ],
  Wisdom: [
    { name: 'Farnam Street', url: 'https://fs.blog/feed/', type: 'educational_blog', weight: 9 },
    { name: 'Aeon Magazine', url: 'https://aeon.co/feed.rss', type: 'philosophy_science_essays', weight: 9 },
    { name: 'MIT News Science & Tech', url: 'https://news.mit.edu/rss/topic/science-technology-and-society', type: 'university_research', weight: 10 },
    { name: 'Quanta Magazine', url: 'https://api.quantamagazine.org/feed/', type: 'science_journalism', weight: 10 },
    { name: 'Stanford Encyclopedia of Philosophy', url: 'https://plato.stanford.edu/rss/sep.xml', type: 'academic_reference', weight: 10 }
  ]
};

function stripHtml_(htmlText) {
  return String(htmlText || '').replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();
}

function collectAllRssInAppsScript(ss) {
  const todayStr = Utilities.formatDate(new Date(), 'Asia/Kolkata', 'yyyy-MM-dd');
  const collected = { Health: [], Wealth: [], Wisdom: [] };
  const sourceRows = [];

  Object.keys(DEFAULT_RSS_SOURCES).forEach(pillar => {
    const tabName = pillar + '_Research';
    DEFAULT_RSS_SOURCES[pillar].forEach(src => {
      let status = 'ok';
      try {
        const resp = UrlFetchApp.fetch(src.url, { muteHttpExceptions: true, followRedirects: true });
        if (resp.getResponseCode() !== 200) {
          status = 'http_' + resp.getResponseCode();
        } else {
          const items = parseRssOrAtomXml_(resp.getContentText(), src, pillar, todayStr);
          collected[pillar] = collected[pillar].concat(items);
          appendUniqueRows_(ss, tabName, items, 'original_article_link');
          status = 'ok (' + items.length + ')';
        }
      } catch (e) {
        status = 'error: ' + e.message;
      }

      sourceRows.push({
        pillar: pillar.toLowerCase(),
        source_name: src.name,
        source_url: src.url,
        source_type: src.type,
        credibility_weight: String(src.weight),
        topics: pillar,
        active: 'TRUE',
        last_checked: new Date().toISOString(),
        last_status: status
      });
    });
  });

  appendUniqueRows_(ss, 'Sources', sourceRows, 'source_url');
  return collected;
}

function parseRssOrAtomXml_(xmlText, src, pillar, todayStr) {
  const doc = XmlService.parse(xmlText);
  const root = doc.getRootElement();
  const rootName = root.getName().toLowerCase();
  const ns = root.getNamespace();
  const results = [];

  let entries = [];
  if (rootName === 'rss') {
    const channel = root.getChild('channel');
    if (channel) entries = channel.getChildren('item');
  } else if (rootName === 'feed') {
    entries = root.getChildren('entry', ns);
  }

  entries.slice(0, 5).forEach(entry => {
    let title = '';
    let link = '';
    let summary = '';
    let pubDate = todayStr;

    if (rootName === 'rss') {
      title = stripHtml_(entry.getChildText('title'));
      link = (entry.getChildText('link') || '').trim();
      summary = stripHtml_(entry.getChildText('description') || '').slice(0, 600);
      pubDate = entry.getChildText('pubDate') || todayStr;
    } else {
      title = stripHtml_(entry.getChildText('title', ns));
      const linkEl = entry.getChild('link', ns);
      link = linkEl && linkEl.getAttribute('href') ? linkEl.getAttribute('href').getValue().trim() : '';
      summary = stripHtml_(entry.getChildText('summary', ns) || entry.getChildText('content', ns) || '').slice(0, 600);
      pubDate = entry.getChildText('updated', ns) || todayStr;
    }

    if (title && link) {
      results.push({
        article_id: Utilities.base64EncodeWebSafe(Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, link)).slice(0, 16),
        source_name: src.name,
        source_url: src.url,
        publication_date: pubDate,
        article_title: title,
        category: pillar,
        original_article_link: link,
        date_collected: todayStr,
        summary: summary,
        credibility_score: String(src.weight),
        relevance_score: String(src.weight),
        claim_classification: 'scientific_or_institutional_report',
        used_in_brief: 'FALSE'
      });
    }
  });
  return results;
}
