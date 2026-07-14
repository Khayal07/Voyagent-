import { useState } from "react";
import { login, register, setAuth } from "../api";
import { useT } from "../i18n";

interface Props {
  onAuthed: (email: string) => void;
}

export default function AuthForm({ onAuthed }: Props) {
  const t = useT();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const resp = mode === "login" ? await login(email, password) : await register(email, password);
      setAuth(resp.token, resp.email);
      onAuthed(resp.email);
    } catch (err) {
      setError(err instanceof Error && err.message !== "Request failed" ? err.message : t.requestFailed);
    } finally {
      setBusy(false);
    }
  };

  const field =
    "w-full rounded-md border border-line bg-void/60 px-3 py-2 text-sm outline-none focus:border-cyan/60 focus:ring-2 focus:ring-cyan/15";
  const label = "mb-1 block font-mono text-[11px] tracking-wider text-ink-soft uppercase";

  return (
    <div className="mx-auto mt-10 w-full max-w-md">
      <form onSubmit={handleSubmit} className="hud-glass p-6">
        <h2 className="font-display text-2xl font-extrabold tracking-tight">{t.authTitle}</h2>
        <p className="mb-6 mt-1 text-sm text-ink-soft">{t.authSubtitle}</p>

        <div className="space-y-4">
          <div>
            <label className={label} htmlFor="email">{t.email}</label>
            <input id="email" type="email" className={field} required autoComplete="email"
              value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>
          <div>
            <label className={label} htmlFor="password">{t.password}</label>
            <input id="password" type="password" className={field} required minLength={8}
              autoComplete={mode === "login" ? "current-password" : "new-password"}
              value={password} onChange={(e) => setPassword(e.target.value)} />
            {mode === "register" && <p className="mt-1 text-xs text-ink-soft">{t.passwordHint}</p>}
          </div>
        </div>

        {error && <p className="mt-4 text-sm text-alert">{error}</p>}

        <button
          type="submit" disabled={busy}
          className="mt-6 w-full rounded-md bg-cyan px-4 py-3 font-display text-base font-semibold text-void transition-shadow hover:shadow-glow-cyan disabled:opacity-50"
        >
          {mode === "login" ? t.login : t.registerAction}
        </button>

        <button
          type="button"
          onClick={() => setMode(mode === "login" ? "register" : "login")}
          className="mt-4 w-full text-center text-sm text-ink-soft hover:text-ink"
        >
          {mode === "login" ? t.needAccount : t.haveAccount}
        </button>
      </form>
    </div>
  );
}
