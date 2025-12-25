import click

from framex.consts import VERSION


@click.group()
@click.version_option(VERSION, prog_name="framex")
def framex() -> None:
    """FrameX command line interface."""


@framex.command()
@click.option(
    "--host",
    default=None,
    help="Host address to bind the FrameX service.",
)
@click.option(
    "--port",
    default=None,
    type=int,
    help="Port number for the FrameX service.",
)
@click.option(
    "--dashboard-host",
    default=None,
    help="Host address for the Ray Dashboard.",
)
@click.option(
    "--dashboard-port",
    default=None,
    type=int,
    help="Port number for the Ray Dashboard.",
)
@click.option(
    "--num-cpus",
    default=None,
    type=int,
    help="Number of CPU cores allocated to Ray.",
)
@click.option("--load-plugins", multiple=True, help="List of external plugins to load. Can be used multiple times.")
@click.option(
    "--load-builtin-plugins", multiple=True, help="List of built-in plugins to load. Can be used multiple times."
)
@click.option(
    "--use-ray/--no-use-ray",
    default=None,
    help="Enable or disable Ray. If not set, use config value.",
)
@click.option(
    "--enable-proxy/--no-enable-proxy",
    default=None,
    help="Enable or disable HTTP proxy. If not set, use config value.",
)
def run(
    host: str | None,
    port: int | None,
    dashboard_host: str | None,
    dashboard_port: int | None,
    num_cpus: int | None,
    load_plugins: tuple[str, ...],
    load_builtin_plugins: tuple[str, ...],
    use_ray: bool | None,
    enable_proxy: bool | None,
) -> None:
    """Run the FrameX service."""
    import framex as fx
    from framex.config import settings

    # Create an updated config instance
    if host is not None:
        settings.server.host = host
    if port is not None:
        settings.server.port = port
    if dashboard_host is not None:
        settings.server.dashboard_host = dashboard_host
    if dashboard_port is not None:
        settings.server.dashboard_port = dashboard_port
    if num_cpus is not None:
        settings.server.num_cpus = num_cpus
    if use_ray is not None:
        settings.server.use_ray = use_ray
    if enable_proxy is not None:
        settings.server.enable_proxy = enable_proxy

    click.echo("🚀 Starting FrameX with configuration:")

    fx.load_plugins(*load_plugins)
    fx.load_builtin_plugins(*load_builtin_plugins)

    fx.run()
