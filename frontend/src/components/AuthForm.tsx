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
    "w-full rounded-lg border border-line bg-bg px-3 py-2 text-sm text-ink outline-none transition-colors placeholder:text-muted focus:border-accent focus:ring-2 focus:ring-accent/20";
  const label = "mb-1 block font-mono text-[11px] tracking-wider text-muted uppercase";

  return (
    <div className="mx-auto mt-10 w-full max-w-md">
      <form onSubmit={handleSubmit} className="panel panel-lg p-6 sm:p-8">
        <h2 className="font-display text-2xl font-semibold tracking-tight">{t.authTitle}</h2>
        <p className="mb-6 mt-1 text-sm text-muted">{t.authSubtitle}</p>

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
            {mode === "register" && <p className="mt-1 text-xs text-muted">{t.passwordHint}</p>}
          </div>
        </div>

        {error && <p className="mt-4 text-sm text-alert">{error}</p>}

        <button
          type="submit" disabled={busy}
          className="mt-6 w-full rounded-lg bg-primary px-4 py-3 text-base font-semibold text-white shadow-panel transition-all hover:bg-primary-deep active:translate-y-px disabled:opacity-50"
        >
          {mode === "login" ? t.login : t.registerAction}
        </button>

        <button
          type="button"
          onClick={() => setMode(mode === "login" ? "register" : "login")}
          className="mt-4 w-full text-center text-sm text-muted transition-colors hover:text-ink"
        >
          {mode === "login" ? t.needAccount : t.haveAccount}
        </button>
      </form>
    </div>
  );
}
