"use client";

import { useState, type FormEvent } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

type AskFormProps = {
  onAsk: (question: string) => void;
  isLoading: boolean;
};

export function AskForm({ onAsk, isLoading }: AskFormProps) {
  const [question, setQuestion] = useState("");

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!question.trim()) return;
    onAsk(question.trim());
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <Input
        placeholder="Ask a research question..."
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        className="flex-1"
        aria-label="Research question"
      />
      <Button type="submit" disabled={isLoading || !question.trim()}>
        {isLoading ? "Asking..." : "Ask"}
      </Button>
    </form>
  );
}
