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

export default function Footer() {
  return (
    <footer className="border-t border-[var(--border)]/80 py-8">
      <div className="mx-auto flex max-w-7xl flex-col gap-3 px-6 text-sm text-[var(--muted-foreground)] md:flex-row md:items-center md:justify-between md:px-10">
        <p>SciFetch by Inigo Rodriguez. Scientific retrieval workspace powered by FastAPI, Next.js and OpenAI.</p>
        <div className="flex flex-wrap items-center gap-4">
          <a
            href="https://github.com/irdsn"
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-2 transition hover:text-[var(--foreground)]"
          >
            <GitHubMark />
            GitHub
          </a>
          <a href="https://github.com/irdsn/SciFetch" target="_blank" rel="noreferrer" className="transition hover:text-[var(--foreground)]">
            Repository
          </a>
        </div>
      </div>
    </footer>
  );
}
