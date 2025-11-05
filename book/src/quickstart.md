## Prerequisites

- Python 3.11+

______________________________________________________________________

## Quick Demo

Create foo.py file

```
from typing import Any
from pydantic import BaseModel

from framex.consts import VERSION
from framex.plugin import BasePlugin, PluginMetadata, on_register, on_request


__plugin_meta__ = PluginMetadata(
    name="foo",
    version=VERSION,
    description="A simple Foo plugin example",
    author="touale",
    url="https://github.com/touale/FrameX-kit",
)


class FooModel(BaseModel):
    text: str = "Hello Foo"


@on_register()
class FooPlugin(BasePlugin):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    @on_request("/foo", methods=["GET"])
    async def foo(self, message: str) -> str:
        return f"Foo says: {message}"

    @on_request("/foo_model", methods=["POST"])
    async def foo_model(self, model: FooModel) -> str:
        return f"Foo received model: {model.text}"#   
```

Run the following command to start the project creation process:

```
$ PYTHONPATH=. framex run --load-plugins foo
🚀 Starting FrameX with configuration:
{
  "host": "127.0.0.1",
  "port": 8080,
  "dashboard_host": "127.0.0.1",
  "dashboard_port": 8260,
  "use_ray": false,
  "enable_proxy": false,
  "num_cpus": 8,
  "excluded_log_paths": []
}
11-05 16:01:13 [SUCCESS] framex.plugin.manage | Succeeded to load plugin "foo" from foo
11-05 16:01:13 [INFO] framex | Start initializing all DeploymentHandle...
11-05 16:01:13 [SUCCESS] framex.plugin.manage | Found plugin HTTP API "['/api/v1/foo', '/api/v1/foo_model']" from plugin(foo)
11-05 16:01:13 [SUCCESS] framex.driver.ingress | Succeeded to register api(['GET']): /api/v1/foo from foo.FooPlugin
11-05 16:01:13 [SUCCESS] framex.driver.ingress | Succeeded to register api(['POST']): /api/v1/foo_model from foo.FooPlugin
INFO:     Started server process [59373]
INFO:     Waiting for application startup.
11-05 16:01:13 [INFO] framex.driver.application | Starting FastAPI application...
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8080 (Press CTRL+C to quit)
```

## Project demo

### Install cookiecutter

Make sure you have Python 3.11 or above installed, then execute the following command in the command line:

```
pip install cookiecutter
```

Cookiecutter is a CLI tool (Command Line Interface) to create an application boilerplate from a template. It uses a templating system — Jinja2 — to replace or customize folder and file names, as well as file content. it can help you quickly create a plugin.

Run the following command to start the project creation process:

```
cookiecutter https://github.com/yourusername/framex-plugin-project-template.git
```

### Project Type

```
[1/17] Select type
  1 - project
  2 - plugin
  Choose from [1/2] (1): 
```

Select **2** for plugin and press Enter to continue.

______________________________________________________________________

### Group Name

```
[2/17] group_name: 
```

This will default based on your selected type.\
You can usually just press **Enter** to accept the default.

______________________________________________________________________

### Project Name

```
[3/17] project_name (Demo Project): 
```

Here you enter the name of your project.\
For example: demo_project.

______________________________________________________________________

### Repository Name

```
[4/17] repo_name (demo_project): 
```

This defaults to the same value as your project name.\
Press **Enter** to accept unless you want a different repo name.

______________________________________________________________________

### CI Tag

```
[5/17] ci_tag (k8s_runner_persionnel_matching): 
```

Generated automatically. Leave as default by pressing **Enter**.

______________________________________________________________________

### Project URL

```
[6/17] project_url (): 
```

Generated automatically. Press **Enter** to accept.

______________________________________________________________________

### Author

```
[7/17] author (touale): 
```

Enter the author name.\
For example: zhangsan.

______________________________________________________________________

### Email

```
[8/17] email (zhangsan@example.com): 
```

Enter the author’s email.\
For example: zhangsan@local.com.

______________________________________________________________________

### Short Description

```
[9/17] short_description (Behold My Awesome Project!): 
```

Press **Enter** to keep the default or type your own description.

______________________________________________________________________

### Version

```
[10/17] version (0.0.0): 
```

Default is fine, press **Enter**.

______________________________________________________________________

### Python Version

```
[11/17] python_version (3.11): 
```

Press **Enter** to use 3.11.

______________________________________________________________________

### Nexus & Other Sources

For the following prompts, press **Enter** to use defaults unless you need custom values:

```
[12/17] nexus_source (https://pypi.org): 
[13/17] primary_pip_source (https://pypi.org/simple): 
[14/17] release_pip_source (https://upload.pypi.org/legacy/): 
[15/17] apt_source (https://mirrors.aliyun.com/): 
[16/17] dockerhub_url (docker.io): 
[17/17] build_image: docker.io/yourusername/demoproject
```

After completing the above operations, you will get the complete project structure:

```
$ tree demo_project 
demo_project
|-- Dockerfile
|-- LICENSE
|-- README.md
|-- data
|   `-- demo@f738
|-- mypy.ini
|-- poe_tasks.toml
|-- pyproject.toml
|-- releaserc.toml
|-- ruff.toml
|-- src
|   `-- demo_project
|       |-- __init__.py
|       |-- __main__.py
|       |-- consts.py
|       |-- log.py
|       `-- plugins
|           |-- __init__.py
|           `-- demo.py
|-- tests
|   |-- __init__.py
|   `-- test_add.py
`-- uv.lock

8 directories, 21 files
```

## Initialize the plugin

After the plugin is created, the initialization template will automatically create a plugin example for you and open interfaces such as `/api/v1/demo_get`, `/api/v1/demo_post`, `/api/v1/demo_stream`.

You can install dependencies using the following command in the project directory. Note that you need to be in the touale intranet:

```
uv sync --dev
```

## Run the plugin

Use the following command to run the plugin:

```
poe server
```

Note that this will start the interface opened by the plugin under src/plugins, and you will see the log as follows:

```
$ poe server
Poe => demo_project
09-03 19:20:02 [SUCCESS] framex.plugin.manage | Succeeded to load plugin "demo" from demo_project.plugins.demo
09-03 19:20:02 [INFO] framex | Start initializing all DeploymentHandle...
09-03 19:20:02 [SUCCESS] framex.plugin.manage | Found plugin HTTP API "/api/v1/demo_get" from plugin(demo)
09-03 19:20:02 [SUCCESS] framex.plugin.manage | Found plugin HTTP API "/api/v1/demo_post" from plugin(demo)
09-03 19:20:02 [SUCCESS] framex.plugin.manage | Found plugin HTTP API "/api/v1/demo_stream" from plugin(demo)
09-03 19:20:02 [SUCCESS] framex.driver.ingress | Succeeded to register api(['GET']): /api/v1/demo_get from demo.DemoPlugin
09-03 19:20:02 [SUCCESS] framex.driver.ingress | Succeeded to register api(['POST']): /api/v1/demo_post from demo.DemoPlugin
09-03 19:20:02 [SUCCESS] framex.driver.ingress | Succeeded to register api(['GET']): /api/v1/demo_stream from demo.DemoPlugin
INFO:     Started server process [10859]
INFO:     Waiting for application startup.
09-03 19:20:02 [INFO] framex.driver.application | Starting FastAPI application...
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8080 (Press CTRL+C to quit)
```

______________________________________________________________________

Visit http://127.0.0.1:8080/docs in your browser and you will see the online documentation
after the framework loads your plugin.

<p align="center">
  <img src="image.png" alt="demo" style="width:90%;">
</p>
