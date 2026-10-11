import { useEffect, useState } from "react";
import { Footer, Header } from "./components/Layout";
import Assessment from "./pages/Assessment";
import Directory from "./pages/Directory";
import Landing from "./pages/Landing";
import LenderDetail from "./pages/LenderDetail";
import Results from "./pages/Results";
import type { EligibilityResponse, Profile } from "./types/api";

const path = () => location.hash.replace(/^#/, "") || "/";
export default function App() {
  const [route, setRoute] = useState(path());
  const [profile, setProfile] = useState<Profile>({});          // kept here so edits survive navigation
  const [result, setResult] = useState<EligibilityResponse | null>(null);
  useEffect(() => { const f = () => { setRoute(path()); window.scrollTo({ top: 0 }); }; window.addEventListener("hashchange", f); return () => window.removeEventListener("hashchange", f); }, []);
  let page;
  if (route.startsWith("/lender/")) page = <LenderDetail id={decodeURIComponent(route.slice(8))} result={result} />;
  else if (route === "/check") page = <Assessment profile={profile} setProfile={setProfile} onResult={setResult} />;
  else if (route === "/results") page = <Results data={result} />;
  else if (route === "/lenders") page = <Directory />;
  else page = <Landing />;
  return <div className="min-h-screen flex flex-col"><Header route={route} /><div className="flex-1">{page}</div><Footer /></div>;
}
