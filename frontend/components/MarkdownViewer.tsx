import { ChevronDown, Download, FileText, LoaderCircle, ShieldCheck } from "lucide-react";
import { useEffect, useId, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

interface HtmlPreviewProps {
  content: string;
  downloadUrl?: string;
  pdfStatus?: "idle" | "pending" | "ready" | "failed";
}

export default function MarkdownViewer({ content, downloadUrl, pdfStatus = "idle" }: HtmlPreviewProps) {
  const hasReport = Boolean(downloadUrl || content);
  const canTogglePreview = Boolean(content);
  const [isDownloading, setIsDownloading] = useState(false);
  const [isPreviewExpanded, setIsPreviewExpanded] = useState(false);
  const previewPanelId = useId();
  const previewDocument = useMemo(() => {
    if (!content) {
      return "";
    }

    return `
      <!doctype html>
      <html lang="en">
        <head>
          <meta charset="utf-8" />
          <meta name="viewport" content="width=device-width, initial-scale=1" />
          <style>
            html, body {
              margin: 0;
              padding: 0;
              background: #eef3f6;
            }
            body {
              min-height: 100vh;
            }
          </style>
        </head>
        <body>
          ${content}
        </body>
      </html>
    `;
  }, [content]);

  useEffect(() => {
    setIsPreviewExpanded(Boolean(content));
  }, [content, downloadUrl]);

  const handleDownload = async () => {
    if (!downloadUrl || isDownloading) {
      return;
    }

    try {
      setIsDownloading(true);
      const response = await fetch(downloadUrl);
      if (!response.ok) {
        throw new Error(`Download failed with status ${response.status}`);
      }

      const blob = await response.blob();
      const blobUrl = window.URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      const filename = downloadUrl.split("/").pop() ?? "scifetch_report.pdf";

      anchor.href = blobUrl;
      anchor.download = filename;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      window.URL.revokeObjectURL(blobUrl);
    } catch (error) {
      console.error(error);
    } finally {
      setIsDownloading(false);
    }
  };

  const handlePreviewToggle = () => {
    if (!canTogglePreview) {
      return;
    }
    setIsPreviewExpanded((currentValue) => !currentValue);
  };

  const handlePreviewHeaderKeyDown = (event: React.KeyboardEvent<HTMLDivElement>) => {
    if (event.key !== "Enter" && event.key !== " ") {
      return;
    }

    event.preventDefault();
    handlePreviewToggle();
  };

  return (
    <Card className="overflow-hidden">
      <CardHeader
        role={canTogglePreview ? "button" : undefined}
        tabIndex={canTogglePreview ? 0 : -1}
        aria-expanded={canTogglePreview ? isPreviewExpanded : undefined}
        aria-controls={canTogglePreview ? previewPanelId : undefined}
        onClick={handlePreviewToggle}
        onKeyDown={handlePreviewHeaderKeyDown}
        className={`border-b border-[var(--border)]/80 bg-white/70 transition-colors ${
          canTogglePreview ? "cursor-pointer hover:bg-white/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ring)] focus-visible:ring-offset-2" : ""
        }`}
      >
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="space-y-1">
            <CardTitle className="flex items-center gap-2 text-2xl">
              <FileText className="size-5 text-[var(--accent)]" />
              Report preview
              <ChevronDown
                className={`ml-1 size-5 text-[var(--muted-foreground)] transition-transform duration-200 ${isPreviewExpanded ? "rotate-180" : ""}`}
              />
            </CardTitle>
            <CardDescription>
              Click this header to expand or collapse the generated report preview. The downloadable PDF remains available at all times.
            </CardDescription>
          </div>

          <div
            className="flex flex-wrap items-center gap-3"
            onClick={(event) => event.stopPropagation()}
            onKeyDown={(event) => event.stopPropagation()}
          >
            <div className="inline-flex items-center gap-2 rounded-full bg-[var(--soft)] px-3 py-1.5 text-xs font-medium text-[var(--soft-foreground)]">
              <ShieldCheck className="size-3.5" />
              HTML preview aligned with PDF output
            </div>
            {downloadUrl ? (
              <Button
                onClick={handleDownload}
                disabled={isDownloading}
                className="text-white [&_svg]:text-white"
              >
                {isDownloading ? <LoaderCircle className="size-4 animate-spin" /> : <Download className="size-4" />}
                Download PDF
              </Button>
            ) : (
              <Button disabled className="opacity-100 disabled:bg-[var(--accent)] disabled:text-white/70">
                {pdfStatus === "pending" ? <LoaderCircle className="size-4 animate-spin" /> : <Download className="size-4" />}
                {pdfStatus === "pending" ? "Generating PDF" : "Download PDF"}
              </Button>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-0">
        {!downloadUrl || !hasReport ? (
          <div className="flex min-h-[420px] flex-col items-center justify-center gap-4 bg-white/75 px-8 py-12 text-center">
            <div className="flex size-14 items-center justify-center rounded-full bg-[var(--soft)] text-[var(--soft-foreground)]">
              <FileText className="size-7" />
            </div>
            <div className="space-y-2">
              <p className="font-[family:var(--font-heading)] text-2xl font-semibold text-[var(--foreground)]">
                Waiting for the next report
              </p>
              <p className="mx-auto max-w-2xl text-[var(--muted-foreground)]">
                Launch a retrieval run to populate this workspace. The preview area will render the generated report inside SciFetch.
              </p>
            </div>
          </div>
        ) : (
          <div id={previewPanelId}>
            {isPreviewExpanded ? (
              previewDocument ? (
                <div className="bg-transparent px-4 py-5 md:px-5 md:py-6">
                  <div className="mx-auto overflow-hidden rounded-[28px] border border-[var(--border)]/70 bg-white/96 shadow-[0_14px_34px_rgba(15,23,42,0.08)]">
                    <div className="flex items-center justify-between border-b border-[var(--border)] bg-[linear-gradient(90deg,rgba(16,32,50,0.96),rgba(16,32,50,0.88))] px-5 py-3 text-sm font-medium text-white">
                      <span>Generated report</span>
                      <span className="text-white/75">Preview</span>
                    </div>
                    <iframe
                      className="min-h-[900px] w-full bg-[#eef3f6]"
                      srcDoc={previewDocument}
                      title="SciFetch report preview"
                    />
                  </div>
                </div>
              ) : (
                <div className="flex min-h-[320px] flex-col items-center justify-center gap-4 bg-white/75 px-8 py-12 text-center">
                  <div className="flex size-14 items-center justify-center rounded-full bg-[var(--soft)] text-[var(--soft-foreground)]">
                    <LoaderCircle className="size-7 animate-spin" />
                  </div>
                  <div className="space-y-2">
                    <p className="font-[family:var(--font-heading)] text-2xl font-semibold text-[var(--foreground)]">
                      Preview unavailable
                    </p>
                    <p className="mx-auto max-w-2xl text-[var(--muted-foreground)]">
                      The backend did not return an HTML preview for this run. The PDF can still be downloaded.
                    </p>
                  </div>
                </div>
              )
            ) : null}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
