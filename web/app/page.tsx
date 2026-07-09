import Link from "next/link";

const quickActions = [
  {
    title: "Search Literature",
    description: "Search academic databases for articles",
    href: "/search",
    icon: "🔍",
  },
  {
    title: "Browse Documents",
    description: "View indexed documents and their content",
    href: "/documents",
    icon: "📄",
  },
  {
    title: "Ask a Question",
    description: "Query your document corpus using AI",
    href: "/ask",
    icon: "💬",
  },
  {
    title: "Ingest Articles",
    description: "Search, download, and index new articles",
    href: "/ingest",
    icon: "📥",
  },
];

export default function HomePage() {
  return (
    <div className="max-w-4xl mx-auto px-4 py-12">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold mb-3">LORNEWS</h1>
        <p className="text-lg text-muted-foreground">
          Academic literature research platform
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {quickActions.map((action) => (
          <Link
            key={action.href}
            href={action.href}
            className="group border rounded-lg p-6 hover:border-primary hover:shadow-sm transition-all"
          >
            <div className="text-2xl mb-2">{action.icon}</div>
            <h2 className="font-semibold mb-1 group-hover:text-primary transition-colors">
              {action.title}
            </h2>
            <p className="text-sm text-muted-foreground">
              {action.description}
            </p>
          </Link>
        ))}
      </div>
    </div>
  );
}
