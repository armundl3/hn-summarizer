"""
Command-line interface for the Hacker News summarizer
"""

import click
from .summarizer import HackerNewsSummarizer


@click.command()
@click.option(
    '--count', '-c',
    default=20,
    help='Number of articles to summarize (default: 20)',
    type=click.IntRange(1, 100)
)
@click.option(
    '--output', '-o',
    type=click.File('w'),
    default='-',
    help='Output file (default: stdout)'
)
def main(count: int, output):
    """Fetch and summarize top Hacker News articles"""
    click.echo(f"Fetching top {count} Hacker News articles...", err=True)
    click.echo("=" * 60, file=output)
    
    summarizer = HackerNewsSummarizer()
    articles = summarizer.summarize_articles(count)
    
    if not articles:
        click.echo("No articles found.", file=output)
        return
    
    for i, article in enumerate(articles, 1):
        click.echo(f"\n--- Article {i} (Score: {article['score']}) ---", file=output)
        for line in article['summary']:
            click.echo(line, file=output)
    
    click.echo("\n" + "=" * 60, file=output)
    click.echo("Summary generation complete!", file=output)


if __name__ == "__main__":
    main()