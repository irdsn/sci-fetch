import * as React from "react";
import { Slot } from "@radix-ui/react-slot";

import { cn } from "@/lib/utils";

type ButtonVariant = "default" | "secondary" | "ghost" | "outline";
type ButtonSize = "default" | "sm" | "lg" | "icon";

const variantStyles: Record<ButtonVariant, string> = {
  default:
    "bg-[var(--accent)] text-[var(--accent-foreground)] shadow-[0_14px_34px_rgba(13,148,136,0.28)] hover:bg-[var(--accent-strong)]",
  secondary:
    "bg-white/80 text-[var(--foreground)] shadow-[0_10px_30px_rgba(15,23,42,0.08)] ring-1 ring-[var(--border)] hover:bg-white",
  ghost:
    "bg-transparent text-[var(--foreground)] hover:bg-white/60",
  outline:
    "bg-transparent text-[var(--foreground)] ring-1 ring-[var(--border)] hover:bg-white/70",
};

const sizeStyles: Record<ButtonSize, string> = {
  default: "h-11 px-5 py-2",
  sm: "h-9 rounded-xl px-4 text-sm",
  lg: "h-12 rounded-2xl px-6 text-base",
  icon: "size-10 rounded-full",
};

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  asChild?: boolean;
  variant?: ButtonVariant;
  size?: ButtonSize;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", size = "default", asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";

    return (
      <Comp
        className={cn(
          "inline-flex items-center justify-center gap-2 rounded-2xl text-sm font-semibold transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ring)] focus-visible:ring-offset-2 focus-visible:ring-offset-transparent disabled:pointer-events-none disabled:opacity-50",
          variantStyles[variant],
          sizeStyles[size],
          className,
        )}
        ref={ref}
        {...props}
      />
    );
  },
);

Button.displayName = "Button";

export { Button };
