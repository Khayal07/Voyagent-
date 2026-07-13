import { createContext, useContext } from "react";

export type Lang = "en" | "az";

export const INTEREST_KEYS = ["history", "nature", "food", "nightlife", "art", "shopping"] as const;

export const translations = {
  en: {
    tagline: "4 AGENTS · 1 ROUTE",
    newTrip: "New trip",
    formTitle: "Where are we going?",
    formSubtitle: "Give the details — four agents will negotiate the best route for you.",
    city: "City",
    cityPlaceholder: "e.g. Rome",
    startDate: "Start",
    endDate: "End",
    budget: "Budget",
    currency: "Currency",
    travelers: "Travelers",
    interests: "Interests",
    submit: "Plan my route",
    submitBusy: "Agents negotiating...",
    errDates: "Invalid date range.",
    errMaxDays: "Trips up to {n} days are supported.",
    requestFailed: "Request failed",
    unknownError: "Unknown error",
    liveChat: "LIVE NEGOTIATION",
    statusActive: "active",
    statusIdle: "ready",
    chatEmpty: "Fill in the form — the agents' negotiation will stream here live.",
    planningWait: "Agents are negotiating your route...",
    noRoute: "No route was produced.",
    all: "All",
    day: "Day",
    totalCost: "Total cost",
    perPerson: "per person",
    startsAt: "starts at",
    minutes: "min",
    people: "travelers",
    agents: {
      interest: "Interest",
      budget: "Budget",
      logistics: "Logistics",
      planner: "Planner",
      system: "System",
    },
    roles: {
      proposal: "PROPOSAL",
      objection: "OBJECTION",
      revision: "NEW PROPOSAL",
      approval: "APPROVED",
      final: "FINAL",
    },
    interestLabels: {
      history: "history",
      nature: "nature",
      food: "food",
      nightlife: "nightlife",
      art: "art",
      shopping: "shopping",
    },
    categories: {
      history: "history",
      nature: "nature",
      food: "food",
      nightlife: "nightlife",
      art: "art",
      shopping: "shopping",
      other: "other",
    },
  },
  az: {
    tagline: "4 AGENT · 1 MARŞRUT",
    newTrip: "Yeni səyahət",
    formTitle: "Hara gedirik?",
    formSubtitle: "Detalları ver — dörd agent sənin üçün ən yaxşı marşrutu müzakirə etsin.",
    city: "Şəhər",
    cityPlaceholder: "məs. Roma",
    startDate: "Başlama",
    endDate: "Bitmə",
    budget: "Büdcə",
    currency: "Valyuta",
    travelers: "Nəfər",
    interests: "Maraqlar",
    submit: "Marşrutu planla",
    submitBusy: "Agentlər danışır...",
    errDates: "Tarix aralığı düzgün deyil.",
    errMaxDays: "Maksimum {n} günlük səyahət dəstəklənir.",
    requestFailed: "Sorğu alınmadı",
    unknownError: "Naməlum xəta",
    liveChat: "CANLI DANIŞIQ",
    statusActive: "gedir",
    statusIdle: "hazır",
    chatEmpty: "Formu doldur — agentlərin danışığı burada canlı axacaq.",
    planningWait: "Agentlər marşrutu müzakirə edir...",
    noRoute: "Marşrut hazırlanmadı.",
    all: "Hamısı",
    day: "Gün",
    totalCost: "Ümumi xərc",
    perPerson: "adambaşı",
    startsAt: "başlayır",
    minutes: "dəq",
    people: "nəfər",
    agents: {
      interest: "Maraq",
      budget: "Büdcə",
      logistics: "Logistika",
      planner: "Planlayıcı",
      system: "Sistem",
    },
    roles: {
      proposal: "TƏKLİF",
      objection: "ETİRAZ",
      revision: "YENİ TƏKLİF",
      approval: "TƏSDİQ",
      final: "YEKUN",
    },
    interestLabels: {
      history: "tarix",
      nature: "təbiət",
      food: "yemək",
      nightlife: "gecə həyatı",
      art: "incəsənət",
      shopping: "alış-veriş",
    },
    categories: {
      history: "tarix",
      nature: "təbiət",
      food: "yemək",
      nightlife: "gecə həyatı",
      art: "incəsənət",
      shopping: "alış-veriş",
      other: "digər",
    },
  },
};

export type Translation = (typeof translations)["en"];

export const LangContext = createContext<{ lang: Lang; setLang: (l: Lang) => void }>({
  lang: "en",
  setLang: () => {},
});

export function useLang() {
  return useContext(LangContext);
}

export function useT(): Translation {
  const { lang } = useContext(LangContext);
  return translations[lang];
}

export function getInitialLang(): Lang {
  const stored = localStorage.getItem("voyagent-lang");
  return stored === "az" || stored === "en" ? stored : "en";
}
