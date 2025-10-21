import click

from framex.config import ServerConfig
from framex.consts import VERSION

_DEFAULT_CONFIG = ServerConfig()


@click.group()
@click.version_option(VERSION, prog_name="framex")
def framex() -> None:
    """FrameX command line interface."""


@framex.command()
@click.option(
    "--host", default=_DEFAULT_CONFIG.host, show_default=True, help="Host address to bind the FrameX service."
)
@click.option("--port", default=_DEFAULT_CONFIG.port, show_default=True, help="Port number for the FrameX service.")
@click.option(
    "--dashboard-host",
    default=_DEFAULT_CONFIG.dashboard_host,
    show_default=True,
    help="Host address for the Ray Dashboard.",
)
@click.option(
    "--dashboard-port",
    default=_DEFAULT_CONFIG.dashboard_port,
    show_default=True,
    help="Port number for the Ray Dashboard.",
)
@click.option(
    "--num-cpus", default=_DEFAULT_CONFIG.num_cpus, show_default=True, help="Number of CPU cores allocated to Ray."
)
@click.option("--load-plugins", multiple=True, help="List of external plugins to load. Can be used multiple times.")
@click.option(
    "--load-builtin-plugins", multiple=True, help="List of built-in plugins to load. Can be used multiple times."
)
def run(
    host: str,
    port: int,
    dashboard_host: str,
    dashboard_port: int,
    num_cpus: int,
    load_plugins: tuple[str],
    load_builtin_plugins: tuple[str],
) -> None:
    """Run the FrameX service."""
    import framex as fx

    # Create an updated config instance
    config = _DEFAULT_CONFIG.model_copy(
        update={
            "host": host,
            "port": port,
            "dashboard_host": dashboard_host,
            "dashboard_port": dashboard_port,
            "num_cpus": num_cpus,
        }
    )

    click.echo("🚀 Starting FrameX with configuration:")
    click.echo(config.model_dump_json(indent=2))

    fx.load_plugins(*load_plugins)
    fx.load_builtin_plugins(*load_builtin_plugins)

    fx.run(
        server_host=config.host,
        server_port=config.port,
        dashboard_host=config.dashboard_host,
        dashboard_port=config.dashboard_port,
        num_cpus=config.num_cpus,
    )
