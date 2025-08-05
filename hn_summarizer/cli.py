"""
Command-line interface for the Hacker News summarizer
"""

import os
import click
from prettytable import PrettyTable
from .summarizer import HackerNewsSummarizer
from .logging_config import setup_logging, get_logger


def _write_markdown_table(articles, output_file):
    """Write articles in markdown table format using prettytable."""
    click.echo("# Hacker News Article Summary\n", file=output_file)
    
    # Create the markdown table manually for better formatting
    click.echo("| # | Title | Score | Summary | URL |", file=output_file)
    click.echo("|---|-------|-------|---------|-----|", file=output_file)
    
    for i, article in enumerate(articles, 1):
        title = article.get("title", "")
        if len(title) > 40:
            title = title[:37] + "..."
        
        score = article.get("score", "")
        
        summary = " / ".join(article.get("summary", []))
        if len(summary) > 60:
            summary = summary[:57] + "..."
        
        url = article.get("url", "")
        if len(url) > 50:
            url = url[:47] + "..."
        
        # Escape pipe characters in content
        title = title.replace("|", "\\|")
        summary = summary.replace("|", "\\|")
        url = url.replace("|", "\\|")
        
        click.echo(f"| {i} | {title} | {score} | {summary} | {url} |", file=output_file)
    
    click.echo("", file=output_file)
    
    # Add enhanced information if available
    for i, article in enumerate(articles, 1):
        if "enhanced" in article and article["enhanced"]:
            enhanced = article["enhanced"]
            click.echo(f"\n## Enhanced Analysis for Article {i}\n", file=output_file)
            
            # Key insights
            click.echo("### Key Insights\n", file=output_file)
            for j, point in enumerate(enhanced.key_points, 1):
                click.echo(f"{j}. {point}", file=output_file)
            
            # Related exploration links
            click.echo("\n### Explore Deeper\n", file=output_file)
            for j, link in enumerate(enhanced.related_links, 1):
                click.echo(f"{j}. {link}", file=output_file)
            
            # Source links
            click.echo("\n### Source Links\n", file=output_file)
            if enhanced.original_url:
                click.echo(f"- [Original Article]({enhanced.original_url})", file=output_file)
            click.echo(f"- [HN Discussion]({enhanced.hn_discussion_url})", file=output_file)


def _write_text_format(articles, output_file):
    """Write articles in traditional text format."""
    for i, article in enumerate(articles, 1):
        score = article["score"]
        click.echo(f"\n--- Article {i} (Score: {score}) ---", file=output_file)
        for line in article["summary"]:
            click.echo(line, file=output_file)
        
        # Display enhanced information if available
        if "enhanced" in article and article["enhanced"]:
            enhanced = article["enhanced"]
            click.echo("\n=== ENHANCED ANALYSIS ===", file=output_file)
            
            # Key insights
            click.echo("\n🔍 KEY INSIGHTS:", file=output_file)
            for j, point in enumerate(enhanced.key_points, 1):
                click.echo(f"  {j}. {point}", file=output_file)
            
            # Related exploration links
            click.echo("\n🔗 EXPLORE DEEPER:", file=output_file)
            for j, link in enumerate(enhanced.related_links, 1):
                click.echo(f"  {j}. {link}", file=output_file)
            
            # Source links
            click.echo("\n📖 SOURCE LINKS:", file=output_file)
            if enhanced.original_url:
                click.echo(f"  • Original Article: {enhanced.original_url}", file=output_file)
            click.echo(f"  • HN Discussion: {enhanced.hn_discussion_url}", file=output_file)


@click.command()
@click.option(
    "--count",
    "-c",
    default=5,
    help="Number of articles to summarize (default: 20)",
    type=click.IntRange(1, 100),
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default=None,
    help="Output file (default: stdout for text, sample/summary.md for markdown)",
)
@click.option(
    "--mode",
    "-m",
    type=click.Choice(["basic", "ollama", "llmapi"]),
    default="basic",
    help="Summarization mode (default: basic)",
)
@click.option(
    "--ollama-model",
    type=str,
    default=None,
    help="Ollama model to use (only applies to ollama mode)",
)
@click.option(
    "--fallback/--no-fallback",
    default=False,
    help="Allow fallback to basic mode if ollama/llmapi fails (default: no fallback)",
)
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], case_sensitive=False),
    default="INFO",
    help="Set logging level (default: INFO)",
)
@click.option(
    "--log-file",
    type=click.Path(),
    default=None,
    help="Log to file instead of stderr",
)
@click.option(
    "--output-format",
    type=click.Choice(["text", "markdown"]),
    default="text",
    help="Output format (default: text)",
)
def main(count: int, output, mode: str, ollama_model: str, fallback: bool, log_level: str, log_file: str, output_format: str):
    """Fetch and summarize top Hacker News articles"""
    # Setup logging first
    setup_logging(level=log_level, log_file=log_file)
    logger = get_logger(__name__)
    
    logger.info(f"Starting HN Summarizer - mode: {mode}, count: {count}, fallback: {fallback}, format: {output_format}")
    if ollama_model:
        logger.info(f"Using custom Ollama model: {ollama_model}")
    
    # Determine output destination
    if output is None:
        if output_format == "markdown":
            output_path = "sample/summary.md"
            # Create sample directory if it doesn't exist
            os.makedirs("sample", exist_ok=True)
        else:
            output_path = "-"  # stdout
    else:
        output_path = output
    
    # Open output file or use stdout
    if output_path == "-":
        output_file = click.get_text_stream('stdout')
    else:
        output_file = open(output_path, 'w')
        logger.info(f"Writing output to: {output_path}")
    
    try:
        click.echo(f"Fetching top {count} Hacker News articles...", err=True)
        if output_format == "text":
            click.echo("=" * 60, file=output_file)

        logger.debug("Initializing HackerNewsSummarizer")
        summarizer = HackerNewsSummarizer(mode=mode, ollama_model=ollama_model, allow_fallback=fallback)
        
        logger.info("Starting article summarization process")
        articles = summarizer.summarize_articles(count)
        
        if not articles:
            logger.warning("No articles found to display")
            click.echo("No articles found.", file=output_file)
            return
        
        logger.info(f"Successfully processed {len(articles)} articles, displaying results")

        if output_format == "markdown":
            _write_markdown_table(articles, output_file)
        else:
            _write_text_format(articles, output_file)

        if output_format == "text":
            click.echo("\n" + "=" * 60, file=output_file)
            click.echo("Summary generation complete!", file=output_file)
        
        logger.info("HN Summarizer completed successfully")
        
    except Exception as e:
        logger.error(f"Summarization failed: {e}", exc_info=True)
        click.echo(f"Error: {e}", err=True)
        if mode != "basic":
            if fallback:
                click.echo("Note: Use --fallback to enable automatic fallback to basic mode.", err=True)
            else:
                click.echo("Hint: You can use --fallback to allow falling back to basic mode on failure.", err=True)
        raise click.Abort()
    finally:
        if output_path != "-":
            output_file.close()


if __name__ == "__main__":
    main()
