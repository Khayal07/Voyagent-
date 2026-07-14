export interface DayWeather {
  code: number;
  t_max: number | null;
  t_min: number | null;
  precip: number | null;
}

/** WMO hava kodu → emoji (Open-Meteo weather_code). */
export function weatherEmoji(code: number): string {
  if (code <= 1) return "☀️";
  if (code <= 3) return "⛅";
  if (code <= 48) return "🌫️";
  if (code <= 57) return "🌦️";
  if (code <= 67) return "🌧️";
  if (code <= 77) return "🌨️";
  if (code <= 82) return "🌧️";
  if (code <= 86) return "🌨️";
  return "⛈️";
}
