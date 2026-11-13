export async function fetchLegacyRates() {
  const r = await fetch("https://rates.example.com/v0/all");
  return r.json();
}
