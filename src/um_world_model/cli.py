import typer

app = typer.Typer()

@app.command()
def status():
    """Show bootstrap status."""
    typer.echo("Bootstrap only; ingestion and evaluation not implemented.")

if __name__ == "__main__":
    app()
