import click


@click.group()
def framex() -> None:
    pass


@framex.command()
def run() -> None:
    import framex

    framex.run()
