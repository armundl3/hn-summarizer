"""
Command-line interface for the Hacker News summarizer
"""

import click
from .summarizer import HackerNewsSummarizer
from .logging_config import setup_logging, get_logger


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
def main(count: int, output, mode: str, ollama_model: str, fallback: bool, log_level: str, log_file: str):
    """Fetch and summarize top Hacker News articles"""
    # Setup logging first
    setup_logging(level=log_level, log_file=log_file)
    logger = get_logger(__name__)
    
    logger.info(f"Starting HN Summarizer - mode: {mode}, count: {count}, fallback: {fallback}")
    if ollama_model:
        logger.info(f"Using custom Ollama model: {ollama_model}")
    
    click.echo(f"Fetching top {count} Hacker News articles...", err=True)
    click.echo("=" * 60, file=output)

    try:
        logger.debug("Initializing HackerNewsSummarizer")
        summarizer = HackerNewsSummarizer(mode=mode, ollama_model=ollama_model, allow_fallback=fallback)
        
        logger.info("Starting article summarization process")
        articles = summarizer.summarize_articles(count)
    except Exception as e:
        logger.error(f"Summarization failed: {e}", exc_info=True)
        click.echo(f"Error: {e}", err=True)
        if mode != "basic":
            if fallback:
                click.echo("Note: Use --fallback to enable automatic fallback to basic mode.", err=True)
            else:
                click.echo("Hint: You can use --fallback to allow falling back to basic mode on failure.", err=True)
        raise click.Abort()

    if not articles:
        logger.warning("No articles found to display")
        click.echo("No articles found.", file=output)
        return
    
    logger.info(f"Successfully processed {len(articles)} articles, displaying results")

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
    
    logger.info("HN Summarizer completed successfully")


if __name__ == "__main__":
    main()
