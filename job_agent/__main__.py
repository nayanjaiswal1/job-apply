import typer

app = typer.Typer(help="Job hunting agent")


@app.command()
def run(
    minimize: bool = typer.Option(False, "--minimize", help="Use min_mode models for every agent"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Run without sending real outreach"),
    agent: str | None = typer.Option(None, "--agent", help="Run a single named agent"),
) -> None:
    from job_agent.startup import ensure_dirs

    ensure_dirs()

    from job_agent.graph import run_graph

    run_graph(minimize=minimize, dry_run=dry_run, agent=agent)


if __name__ == "__main__":
    app()
