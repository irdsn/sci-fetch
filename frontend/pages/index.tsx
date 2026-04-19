import Head from "next/head";
import { Activity, AlertCircle, ArrowUpRight, Bot, DatabaseZap, FlaskConical, LoaderCircle, Sparkles } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import Footer from "@/components/Footer";
import InputForm from "@/components/InputForm";
import MarkdownViewer from "@/components/MarkdownViewer";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const statusSteps = [
  "Query orchestration",
  "Academic retrieval",
  "Evidence synthesis",
  "PDF rendering",
];

const sourceBadges = ["PubMed", "arXiv", "OpenAlex", "Europe PMC", "CrossRef"];
const defaultApiBaseUrl = "http://127.0.0.1:8000";

function GitHubMark() {
  return (
    <svg
      aria-hidden="true"
      className="size-4"
      fill="currentColor"
      viewBox="0 0 24 24"
    >
      <path d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.009-.866-.014-1.699-2.782.605-3.369-1.343-3.369-1.343-.455-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.004.071 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.091-.647.349-1.088.635-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.027A9.564 9.564 0 0 1 12 6.844a9.55 9.55 0 0 1 2.504.337c1.909-1.297 2.748-1.027 2.748-1.027.546 1.378.202 2.397.1 2.65.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.31.678.921.678 1.857 0 1.34-.012 2.421-.012 2.75 0 .268.18.58.688.481A10.02 10.02 0 0 0 22 12.017C22 6.484 17.523 2 12 2Z" />
    </svg>
  );
}

export default function Home() {
  const [prompt, setPrompt] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [htmlPreview, setHtmlPreview] = useState("");
  const [downloadUrl, setDownloadUrl] = useState("");
  const [pdfStatus, setPdfStatus] = useState<"idle" | "pending" | "ready" | "failed">("idle");
  const [statusUrl, setStatusUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [warning, setWarning] = useState("");
  const pollingIntervalRef = useRef<number | null>(null);

  const canSubmit = prompt.trim().length > 0 && apiKey.trim().length > 0;
  const apiBaseUrl = process.env.NEXT_PUBLIC_SCIFETCH_API ?? defaultApiBaseUrl;

  const heroMetrics = [
    { label: "Sources", value: "5 academic APIs" },
    { label: "Output", value: "Preview + PDF" },
    { label: "Mode", value: "Autonomous retrieval" },
  ];

  useEffect(() => {
    return () => {
      if (pollingIntervalRef.current) {
        window.clearInterval(pollingIntervalRef.current);
      }
    };
  }, []);

  useEffect(() => {
    if (!statusUrl || pdfStatus !== "pending") {
      return;
    }

    const pollStatus = async () => {
      try {
        const response = await fetch(statusUrl);
        if (!response.ok) {
          throw new Error(`Status check failed with status ${response.status}`);
        }

        const statusPayload = await response.json();
        const nextStatus = statusPayload.status as "pending" | "ready" | "failed";
        setPdfStatus(nextStatus);

        if (statusPayload.download_url) {
          setDownloadUrl(statusPayload.download_url);
        }

        if (statusPayload.pdf_warning) {
          setWarning(statusPayload.pdf_warning);
        }

        if (nextStatus !== "pending" && pollingIntervalRef.current) {
          window.clearInterval(pollingIntervalRef.current);
          pollingIntervalRef.current = null;
        }
      } catch (statusError) {
        console.error(statusError);
        setPdfStatus("failed");
        setWarning("The PDF generation status could not be confirmed. Try running the request again.");
        if (pollingIntervalRef.current) {
          window.clearInterval(pollingIntervalRef.current);
          pollingIntervalRef.current = null;
        }
      }
    };

    void pollStatus();
    pollingIntervalRef.current = window.setInterval(() => {
      void pollStatus();
    }, 3000);

    return () => {
      if (pollingIntervalRef.current) {
        window.clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
    };
  }, [pdfStatus, statusUrl]);

  const handleRunAgent = async () => {
    if (!prompt.trim()) {
      setError("Please provide a research prompt before launching the pipeline.");
      return;
    }

    if (!apiKey.trim()) {
      setError("Please provide a valid OpenAI API key.");
      return;
    }

    setLoading(true);
    setError("");
    setWarning("");
    setHtmlPreview("");
    setDownloadUrl("");
    setStatusUrl("");
    setPdfStatus("idle");
    if (pollingIntervalRef.current) {
      window.clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }

    try {
      const response = await fetch(`${apiBaseUrl}/run`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          prompt,
          api_key: apiKey,
        }),
      });

      if (!response.ok) {
        let detail = `Backend request failed with status ${response.status}`;

        try {
          const errorPayload = (await response.json()) as { detail?: string };
          if (errorPayload.detail) {
            detail = errorPayload.detail;
          }
        } catch {
          // Keep the generic fallback when the response body is not JSON.
        }

        throw new Error(detail);
      }

      const data = await response.json();
      setHtmlPreview(data.html_preview ?? "");
      setDownloadUrl(data.pdf_status === "ready" ? (data.download_url ?? "") : "");
      setWarning(data.pdf_warning ?? "");
      setStatusUrl(data.status_url ?? "");
      setPdfStatus(data.pdf_status ?? (data.download_url ? "ready" : "idle"));
    } catch (requestError) {
      console.error(requestError);
      const message =
        requestError instanceof Error
          ? requestError.message
          : "SciFetch could not complete the request. Check the backend URL, your API key, and try again.";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Head>
        <title>SciFetch</title>
        <meta
          name="description"
          content="Autonomous scientific literature workspace for retrieval, synthesis and PDF reporting."
        />
      </Head>

      <main className="relative overflow-hidden">
        <div className="absolute inset-0 -z-20 bg-[radial-gradient(circle_at_top_left,_rgba(13,148,136,0.18),_transparent_28%),radial-gradient(circle_at_top_right,_rgba(14,116,144,0.16),_transparent_32%),linear-gradient(180deg,_#f4fbfa_0%,_#eef5f8_42%,_#fbf7ef_100%)]" />
        <div className="absolute inset-0 -z-10 bg-[linear-gradient(rgba(15,23,42,0.03)_1px,_transparent_1px),linear-gradient(90deg,rgba(15,23,42,0.03)_1px,_transparent_1px)] bg-[size:32px_32px] [mask-image:linear-gradient(180deg,white,rgba(255,255,255,0.2))]" />

        <section className="mx-auto flex min-h-screen w-full max-w-7xl flex-col px-6 pb-16 pt-8 md:px-10">
          <div className="mb-8 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex size-11 items-center justify-center rounded-2xl bg-[var(--ink)] text-white shadow-[0_18px_34px_rgba(15,23,42,0.25)]">
                <Bot className="size-5" />
              </div>
              <div>
                <p className="font-[family:var(--font-heading)] text-xl font-bold tracking-tight text-[var(--foreground)]">
                  SciFetch
                </p>
                <p className="text-sm text-[var(--muted-foreground)]">Scientific intelligence workspace</p>
              </div>
            </div>

            <Button asChild variant="ghost" className="hidden sm:inline-flex">
              <a href="https://github.com/irdsn/SciFetch" target="_blank" rel="noreferrer">
                <GitHubMark />
                Repository
                <ArrowUpRight className="size-4" />
              </a>
            </Button>
          </div>

          <div className="space-y-8">
            <div className="space-y-5">
              <div className="space-y-4">
                <div className="space-y-3 text-center">
                  <h1 className="w-full font-[family:var(--font-heading)] text-5xl font-bold leading-none tracking-[-0.04em] text-[var(--foreground)] md:text-7xl">
                    SciFetch
                  </h1>
                  <p className="mx-auto max-w-4xl font-[family:var(--font-heading)] text-2xl font-medium leading-tight text-[var(--soft-foreground)] md:text-3xl">
                    Research faster with a retrieval pipeline built for scientific work.
                  </p>
                </div>
                <div className="flex justify-start">
                  <Badge className="bg-white/90 text-[var(--soft-foreground)]">AI-powered literature retrieval</Badge>
                </div>
                <p className="w-full max-w-none text-lg leading-8 text-[var(--muted-foreground)] [text-align:justify]">
                  SciFetch is an autonomous AI agent designed to search, synthesize, and generate scientific literature
                  reports based on natural language prompts. It leverages modern AI and web technologies, LangChain for
                  autonomous reasoning, OpenAI for summarization, and academic APIs for up-to-date content retrieval.
                  The final output is delivered as a styled, downloadable PDF report, accessible via a clean web
                  interface, with a clear path from query to reviewable output.
                </p>
              </div>

              <div className="grid gap-4 lg:grid-cols-[1.35fr_0.8fr_0.8fr]">
                {heroMetrics.map((metric) => (
                  <Card key={metric.label} className="bg-white/70">
                    <CardContent className="p-5">
                      <p className="text-sm text-[var(--muted-foreground)]">{metric.label}</p>
                      <p className="mt-2 text-center font-[family:var(--font-heading)] text-2xl font-semibold text-[var(--foreground)]">
                        {metric.value}
                      </p>
                      {metric.label === "Sources" ? (
                        <div className="mt-4 flex flex-wrap justify-center gap-2">
                          {sourceBadges.map((source) => (
                            <Badge key={source}>{source}</Badge>
                          ))}
                        </div>
                      ) : null}
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>

            <div className="grid items-stretch gap-6 lg:grid-cols-[1.18fr_0.82fr]">
              <Card className="relative overflow-hidden">
                <div className="absolute inset-x-0 top-0 h-1 bg-[linear-gradient(90deg,var(--accent),var(--highlight))]" />
                <CardHeader className="pb-5">
                  <CardTitle className="text-3xl font-[family:var(--font-heading)]">Launch a new retrieval run</CardTitle>
                  <CardDescription>
                    Provide a focused brief and a request-scoped OpenAI key. The backend retrieves papers, writes the
                    synthesis and renders the PDF in a single pass.
                  </CardDescription>
                  <div className="inline-flex items-center gap-2 text-sm text-[var(--muted-foreground)]">
                    <Sparkles className="size-4 text-[var(--accent)]" />
                    Multi-source retrieval, synthesis and PDF export in one run
                  </div>
                </CardHeader>
                <CardContent className="flex h-full flex-col space-y-5">
                  <InputForm
                    prompt={prompt}
                    setPrompt={setPrompt}
                    apiKey={apiKey}
                    setApiKey={setApiKey}
                    onSubmit={handleRunAgent}
                    loading={loading}
                  />

                  {error ? (
                    <div className="flex items-start gap-3 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
                      <AlertCircle className="mt-0.5 size-4 shrink-0" />
                      <span>{error}</span>
                    </div>
                  ) : null}

                  {warning ? (
                    <div className="flex items-start gap-3 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
                      <AlertCircle className="mt-0.5 size-4 shrink-0" />
                      <span>{warning}</span>
                    </div>
                  ) : null}

                  {!canSubmit ? (
                    <p className="mt-auto text-center text-xs text-[var(--muted-foreground)]">
                      Fill in the brief and API key to activate the pipeline.
                    </p>
                  ) : null}

                  {loading ? (
                    <div className="mt-auto rounded-[24px] border border-[var(--border)] bg-[linear-gradient(135deg,rgba(15,118,110,0.08),rgba(216,161,30,0.08))] p-5">
                      <div className="flex items-center gap-3">
                        <div className="flex size-11 items-center justify-center rounded-2xl bg-[var(--soft)] text-[var(--soft-foreground)]">
                          <LoaderCircle className="size-5 animate-spin" />
                        </div>
                        <div>
                          <p className="font-medium text-[var(--foreground)]">Pipeline in progress</p>
                          <p className="text-sm text-[var(--muted-foreground)]">
            Querying sources, aggregating papers and preparing the preview.
                          </p>
                        </div>
                      </div>
                      <div className="mt-4 h-2 overflow-hidden rounded-full bg-white/90">
                        <div className="h-full w-1/2 animate-[pulse_1.4s_ease-in-out_infinite] rounded-full bg-[linear-gradient(90deg,var(--accent),var(--highlight))]" />
                      </div>
                    </div>
                  ) : (
                    <div className="mt-auto" />
                  )}
                </CardContent>
              </Card>

              <div className="grid gap-6">
                <Card className="bg-[linear-gradient(180deg,rgba(15,23,42,0.96)_0%,rgba(15,23,42,0.88)_100%)] text-white shadow-[0_28px_80px_rgba(15,23,42,0.24)]">
                  <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-2xl font-[family:var(--font-heading)]">
                    <Activity className="size-5 text-[var(--highlight)]" />
                    Run status
                  </CardTitle>
                  <CardDescription className="text-slate-300">
                    The current frontend can only show global progress, but the visual language is already structured
                    for richer backend telemetry later.
                  </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {statusSteps.map((step, index) => {
                      const isActive = loading && index === 1;
                      const isComplete = htmlPreview.length > 0 || (!loading && index === 0);

                      return (
                        <div
                          key={step}
                          className={`flex items-center justify-between rounded-2xl border px-4 py-3 ${
                            isActive
                              ? "border-emerald-300/40 bg-emerald-400/10"
                              : "border-white/10 bg-white/5"
                          }`}
                        >
                          <div className="flex items-center gap-3">
                            <div
                              className={`size-2.5 rounded-full ${
                                isActive ? "bg-emerald-300 shadow-[0_0_20px_rgba(110,231,183,0.8)]" : "bg-slate-500"
                              }`}
                            />
                            <span className="text-sm font-medium text-slate-100">{step}</span>
                          </div>
                          <span className="text-xs uppercase tracking-[0.22em] text-slate-300">
                            {pdfStatus === "ready"
                              ? "Ready"
                              : pdfStatus === "pending"
                                ? "Rendering"
                                : htmlPreview
                                  ? "Ready"
                                  : isActive
                                    ? "Active"
                                    : isComplete
                                      ? "Primed"
                                      : "Queued"}
                          </span>
                        </div>
                      );
                    })}
                  </CardContent>
                </Card>

                <div className="grid gap-4">
                  <Card className="bg-white/75">
                    <CardContent className="flex items-center gap-4 p-5">
                      <div className="flex size-11 shrink-0 items-center justify-center self-center rounded-2xl bg-[var(--soft)] text-[var(--soft-foreground)]">
                        <DatabaseZap className="size-5" />
                      </div>
                      <div className="space-y-2">
                        <p className="font-medium text-[var(--foreground)]">Multi-source aggregation</p>
                        <p className="text-sm leading-6 text-[var(--muted-foreground)]">
                          Parallel retrieval across biomedical and multidisciplinary repositories with a unified metadata contract.
                        </p>
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="bg-white/75">
                    <CardContent className="flex items-center gap-4 p-5">
                      <div className="flex size-11 shrink-0 items-center justify-center self-center rounded-2xl bg-[var(--soft)] text-[var(--soft-foreground)]">
                        <FlaskConical className="size-5" />
                      </div>
                      <div className="space-y-2">
                        <p className="font-medium text-[var(--foreground)]">Report-ready output</p>
                        <p className="text-sm leading-6 text-[var(--muted-foreground)]">
                          The generated report is previewed in-browser and preserved as a downloadable PDF artifact.
                        </p>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </div>
            </div>
          </div>

          <section className="mt-10 space-y-6">
            <div className="flex items-center gap-3">
              <Sparkles className="size-5 text-[var(--accent)]" />
              <div>
                <h2 className="font-[family:var(--font-heading)] text-3xl font-semibold tracking-tight text-[var(--foreground)]">
                  Output workspace
                </h2>
                <p className="text-[var(--muted-foreground)]">
                  Preview the generated PDF directly in the workspace and download that exact same artifact when needed.
                </p>
              </div>
            </div>

            <MarkdownViewer content={htmlPreview} downloadUrl={downloadUrl} pdfStatus={pdfStatus} />
          </section>
        </section>

        <Footer />
      </main>
    </>
  );
}
