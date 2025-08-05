"""
Command-line interface for the Hacker News summarizer
"""

import click
from .summarizer import HackerNewsSummarizer


@click.command()
@click.option(
    "--count",
    "-c",
    default=20,
    help="Number of articles to summarize (default: 20)",
    type=click.IntRange(1, 100),
)
@click.option(
    "--output",
    "-o",
    type=click.File("w"),
    default="-",
    help="Output file (default: stdout)",
)
@click.option(
    "--mode",
    "-m",
    type=click.Choice(["basic", "ollama", "llmapi"]),
    default="basic",
    help="Summarization mode (default: basic)",
)
def main(count: int, output, mode: str):
    """Fetch and summarize top Hacker News articles"""
    click.echo(f"Fetching top {count} Hacker News articles...", err=True)
    click.echo("=" * 60, file=output)

    summarizer = HackerNewsSummarizer(mode=mode)
    articles = summarizer.summarize_articles(count)

    if not articles:
        click.echo("No articles found.", file=output)
        return

    for i, article in enumerate(articles, 1):
        score = article["score"]
        click.echo(f"\n--- Article {i} (Score: {score}) ---", file=output)
        for line in article["summary"]:
            click.echo(line, file=output)
        
        # Display enhanced information if available
        if "enhanced" in article and article["enhanced"]:
            enhanced = article["enhanced"]
            click.echo("\n=== ENHANCED ANALYSIS ===", file=output)
            
            # Key insights
            click.echo("\n🔍 KEY INSIGHTS:", file=output)
            for j, point in enumerate(enhanced.key_points, 1):
                click.echo(f"  {j}. {point}", file=output)
            
            # Related exploration links
            click.echo("\n🔗 EXPLORE DEEPER:", file=output)
            for j, link in enumerate(enhanced.related_links, 1):
                click.echo(f"  {j}. {link}", file=output)
            
            # Source links
            click.echo("\n📖 SOURCE LINKS:", file=output)
            if enhanced.original_url:
                click.echo(f"  • Original Article: {enhanced.original_url}", file=output)
            click.echo(f"  • HN Discussion: {enhanced.hn_discussion_url}", file=output)

    click.echo("\n" + "=" * 60, file=output)
    click.echo("Summary generation complete!", file=output)


if __name__ == "__main__":
    main()
