import * as React from "react";

import { cn } from "@/lib/utils";

function Badge({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "inline-flex items-center rounded-full border border-[var(--border)] bg-white/80 px-3 py-1 text-xs font-medium text-[var(--muted-foreground)] backdrop-blur",
        className,
      )}
      {...props}
    />
  );
}

export { Badge };
