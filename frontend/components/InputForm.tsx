import { ArrowRight, KeyRound, LoaderCircle, Telescope } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

interface InputFormProps {
  prompt: string;
  setPrompt: (value: string) => void;
  apiKey: string;
  setApiKey: (value: string) => void;
  onSubmit: () => void;
  loading: boolean;
}

export default function InputForm({
  prompt,
  setPrompt,
  apiKey,
  setApiKey,
  onSubmit,
  loading,
}: InputFormProps) {
  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    onSubmit();
  };

  return (
    <form className="space-y-5" onSubmit={handleSubmit}>
      <div className="space-y-2">
        <label className="flex items-center gap-2 text-sm font-medium text-[var(--foreground)]" htmlFor="prompt">
          <Telescope className="size-4 text-[var(--accent)]" />
          Research brief
        </label>
        <Textarea
          id="prompt"
          value={prompt}
          onChange={(event) => setPrompt(event.target.value)}
          placeholder="Examples: Cancer detection using AI | Applications of self-supervised learning in genomics | Recent advances in quantum machine learning | Federated learning for medical imaging"
          rows={7}
        />
      </div>

      <div className="space-y-2">
        <label className="flex items-center gap-2 text-sm font-medium text-[var(--foreground)]" htmlFor="apiKey">
          <KeyRound className="size-4 text-[var(--accent)]" />
          OpenAI API key
        </label>
        <Input
          id="apiKey"
          type="password"
          value={apiKey}
          onChange={(event) => setApiKey(event.target.value)}
          placeholder="sk-..."
        />
      </div>

      <div className="flex justify-center pt-1">
        <Button className="group min-w-[330px] px-12 !text-[1.35rem] !leading-none" size="lg" type="submit" disabled={loading}>
          {loading ? (
            <>
              <LoaderCircle className="size-4 animate-spin" />
              Fetching Articles...
            </>
          ) : (
            <>
              Launch SciFetch
              <ArrowRight className="size-4 transition-transform duration-200 group-hover:translate-x-0.5" />
            </>
          )}
        </Button>
      </div>
    </form>
  );
}
