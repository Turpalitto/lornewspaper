"""CLI for ResearchAgent."""

from __future__ import annotations

import argparse
import asyncio
import sys


def _run_async(coro):
    return asyncio.run(coro)


async def cmd_search(args):
    from research_agent import ResearchAgent
    async with ResearchAgent() as agent:
        result = await agent.search(args.query, max_results=args.max)
        for a in result.articles[:10]:
            title = a.get("title", "?")[:80]
            print(f"  {a.get('id', '?'):>8}  {title}")
        print(f"\n{len(result.articles)} articles found in {result.elapsed_ms}ms")


async def cmd_ingest(args):
    from research_agent import ResearchAgent
    async with ResearchAgent() as agent:
        result = await agent.ingest(args.query, max_results=args.max)
        for d in result.documents:
            title = (d.metadata or {}).get("title", d.document_id)
            print(f"  Indexed: {title} ({d.statistics.total_chunks} chunks)")
        print(f"\n{len(result.documents)} documents indexed in {result.elapsed_ms}ms")


async def cmd_ask(args):
    from research_agent import ResearchAgent
    async with ResearchAgent() as agent:
        result = await agent.ask(args.question)
        if result.answer:
            print(f"\n{result.answer.answer}\n")
            if result.answer.sources:
                print(f"Sources: {', '.join(result.answer.sources)}")
            print(f"Confidence: {result.answer.confidence:.2f}")
        if result.error:
            print(f"Error: {result.error}", file=sys.stderr)


async def cmd_summarize(args):
    from research_agent import ResearchAgent
    async with ResearchAgent() as agent:
        result = await agent.summarize(args.document_id)
        if result.answer:
            print(f"\n{result.answer.answer}\n")
        if result.error:
            print(f"Error: {result.error}", file=sys.stderr)


async def cmd_similar(args):
    from research_agent import ResearchAgent
    async with ResearchAgent() as agent:
        result = await agent.similar(args.document_id)
        if result.answer:
            print(f"\n{result.answer.answer}\n")
        if result.error:
            print(f"Error: {result.error}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="ResearchAgent CLI")
    sub = parser.add_subparsers(dest="command")

    p_search = sub.add_parser("search", help="Search academic literature")
    p_search.add_argument("query")
    p_search.add_argument("--max", type=int, default=10)
    p_search.set_defaults(func=cmd_search)

    p_ingest = sub.add_parser("ingest", help="Search, download, process, and index")
    p_ingest.add_argument("query")
    p_ingest.add_argument("--max", type=int, default=5)
    p_ingest.set_defaults(func=cmd_ingest)

    p_ask = sub.add_parser("ask", help="Ask a question about indexed documents")
    p_ask.add_argument("question")
    p_ask.set_defaults(func=cmd_ask)

    p_sum = sub.add_parser("summarize", help="Summarize an indexed document")
    p_sum.add_argument("document_id")
    p_sum.set_defaults(func=cmd_summarize)

    p_sim = sub.add_parser("similar", help="Find similar documents")
    p_sim.add_argument("document_id")
    p_sim.set_defaults(func=cmd_similar)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)
    _run_async(args.func(args))


if __name__ == "__main__":
    main()