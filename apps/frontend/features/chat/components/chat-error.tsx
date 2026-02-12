interface ChatErrorProps {
  error: string;
}

export function ChatError({ error }: ChatErrorProps) {
  return (
    <div className="rounded-xl border border-destructive/40 bg-destructive/10 px-4 py-3 text-sm text-destructive">
      {error}
    </div>
  );
}
