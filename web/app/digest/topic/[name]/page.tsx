"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ErrorBoundary } from "@/components/shared/error-boundary";
import { LoadingState } from "@/components/shared/loading-state";
import { DigestCard } from "@/components/digest/digest-card";

type DigestItem = {
  id: string;
  title: string;
  authors: string[];
  journal: string;
  doi: string;
  study_design: string;
  evidence_level: string;
  clinical_importance: number;
  summary_bullets: string[];
  tags: string[];
};

type Topic = {
  id: string;
  display_name: string;
  icon: string;
  paper_count: number;
  summary: string;
  items: DigestItem[];
};

const TOPIC_DISPLAY: Record<string, { name: string; icon: string }> = {
  otology: { name: "Otology", icon: "🦻" },
  rhinology: { name: "Rhinology", icon: "👃" },
  laryngology: { name: "Laryngology", icon: "🗣️" },
  head_neck_surgery: { name: "Head & Neck Surgery", icon: "🏥" },
  audiology: { name: "Audiology", icon: "🔊" },
  vestibular: { name: "Vestibular Disorders", icon: "🌀" },
  sleep_medicine: { name: "Sleep Medicine", icon: "😴" },
  pediatric_ent: { name: "Pediatric ENT", icon: "👶" },
  facial_plastic_surgery: { name: "Facial Plastic Surgery", icon: "✨" },
  skull_base: { name: "Skull Base Surgery", icon: "🧠" },
  general_ent: { name: "General ENT", icon: "📋" },
};

export default function TopicDigestPage() {
  const params = useParams();
  const name = params.name as string;
  const [topic, setTopic] = useState<Topic | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const res = await fetch(`/api/v1/digest/topic/${name}`);
        if (!res.ok) throw new Error(`Failed: ${res.statusText}`);
        setTopic(await res.json());
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load");
      } finally {
        setIsLoading(false);
      }
    }
    load();
  }, [name]);

  const display = TOPIC_DISPLAY[name] || { name, icon: "📄" };

  return (
    <ErrorBoundary>
      <div className="max-w-5xl mx-auto px-4 py-8 space-y-8">
        <div>
          <Link href="/digest" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
            &larr; Back to digest
          </Link>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-3xl">{display.icon}</span>
          <div>
            <h1 className="text-2xl font-bold">{display.name}</h1>
            <p className="text-sm text-muted-foreground">
              {topic ? `${topic.paper_count} papers` : "Loading..."}
            </p>
          </div>
        </div>

        {isLoading && <LoadingState count={3} />}

        {error && (
          <Card>
            <CardContent className="pt-6">
              <p className="text-destructive">{error}</p>
            </CardContent>
          </Card>
        )}

        {topic && (
          <>
            {topic.summary && (
              <Card>
                <CardContent className="pt-6">
                  <p className="text-sm text-muted-foreground">{topic.summary}</p>
                </CardContent>
              </Card>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {topic.items.map((item) => (
                <DigestCard key={item.id} item={item} />
              ))}
            </div>

            {topic.items.length === 0 && (
              <p className="text-center text-muted-foreground py-8">
                No papers in this topic for the current period.
              </p>
            )}
          </>
        )}
      </div>
    </ErrorBoundary>
  );
}
