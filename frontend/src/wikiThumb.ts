// OSM wikipedia tagı ("it:Fontana di Trevi") → Wikipedia REST summary thumbnail URL-i.
// CORS açıqdır; nəticələr modul səviyyəsində cache-lənir, xəta → null.
const cache = new Map<string, Promise<string | null>>();

export function getThumb(wiki: string): Promise<string | null> {
  if (!cache.has(wiki)) {
    cache.set(wiki, fetchThumb(wiki));
  }
  return cache.get(wiki)!;
}

async function fetchThumb(wiki: string): Promise<string | null> {
  const sep = wiki.indexOf(":");
  if (sep < 1) return null;
  const lang = wiki.slice(0, sep);
  const title = wiki.slice(sep + 1).replace(/ /g, "_");
  try {
    const resp = await fetch(
      `https://${lang}.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(title)}`,
    );
    if (!resp.ok) return null;
    const data = await resp.json();
    return data.thumbnail?.source ?? null;
  } catch {
    return null;
  }
}
