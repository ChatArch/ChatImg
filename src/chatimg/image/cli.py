from chatimg import __version__
import click
from chatstyle import (
    CommandField,
    CommandSchema,
    add_interactive_option,
    resolve_command_inputs,
)
from chatimg.image import create_generator
from chatimg.image.helpers import (
    download_binary,
    echo_model_list,
    resolve_generated_output_path,
    save_binary,
)


PROMPT_SCHEMA = CommandSchema(
    name="image-prompt",
    fields=(CommandField("prompt", prompt="prompt", required=True),),
)


HF_GENERATE_SCHEMA = CommandSchema(
    name="image-huggingface-generate",
    fields=(
        CommandField("prompt", prompt="prompt", required=True),
    ),
)


def _short_help(command):
    """Return the first help sentence for a Click command."""

    help_text = (command.short_help or command.help or "").strip()
    if not help_text:
        return ""
    return help_text.splitlines()[0].strip()


def _format_argument(argument):
    metavar = (argument.metavar or argument.name or "ARG").upper().replace("_", "-")
    if argument.nargs != 1:
        metavar = f"{metavar}..."
    if argument.required:
        return metavar
    return f"[{metavar}]"


def _format_option(option):
    visible = [flag for flag in option.opts if flag.startswith("--")]
    visible.extend(flag for flag in option.opts if flag not in visible)
    if not visible:
        return ""
    flag = visible[0]
    if option.is_flag or option.flag_value is not None:
        return f"[{flag}]"
    metavar = (option.metavar or option.name or "VALUE").upper().replace("_", "-")
    return f"[{flag} {metavar}]"


def _format_signature(command):
    parts = []
    for param in command.params:
        if getattr(param, "hidden", False):
            continue
        if isinstance(param, click.Argument):
            parts.append(_format_argument(param))
        elif isinstance(param, click.Option):
            if param.name in {"help", "version", "tree"}:
                continue
            item = _format_option(param)
            if item:
                parts.append(item)
    return " " + " ".join(parts) if parts else ""


def _click_group_children(command):
    if not isinstance(command, click.Group):
        return []
    ctx = click.Context(command, info_name=command.name)
    return [(name, command.get_command(ctx, name)) for name in command.list_commands(ctx)]


def _tree_command_line(command, path):
    line = f"{path}{_format_signature(command)}"
    help_text = _short_help(command)
    if help_text:
        line = f"{line} # {help_text}"
    return line


def _render_click_command(command, path, prefix="", is_last=True):
    connector = "└── " if is_last else "├── "
    lines = [f"{prefix}{connector}{_tree_command_line(command, path)}"]
    children = [(name, child) for name, child in _click_group_children(command) if child]
    child_prefix = prefix + ("    " if is_last else "│   ")
    for index, (name, child) in enumerate(children):
        child_path = f"{path} {name}"
        lines.extend(
            _render_click_command(
                child,
                child_path,
                prefix=child_prefix,
                is_last=index == len(children) - 1,
            )
        )
    return lines


def render_cli_tree(command):
    """Render the real registered Click command tree."""

    root_name = command.name or "chatimg"
    lines = [_tree_command_line(command, root_name)]
    root_entries = [
        ("--help", "Show this message and exit."),
        ("--version", "Show the version and exit."),
        ("--tree", "Print the registered command tree."),
    ]
    children = [(name, child) for name, child in _click_group_children(command) if child]
    entries = [("pseudo", option, help_text) for option, help_text in root_entries] + [
        ("command", name, child) for name, child in children
    ]
    for index, entry in enumerate(entries):
        is_last = index == len(entries) - 1
        connector = "└── " if is_last else "├── "
        if entry[0] == "pseudo":
            lines.append(f"{connector}{entry[1]} # {entry[2]}")
        else:
            _, name, child = entry
            lines.extend(_render_click_command(child, name, is_last=is_last))
    return "\n".join(lines)


def _print_cli_tree(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return None
    click.echo(render_cli_tree(ctx.command))
    ctx.exit()


@click.group(name="chatimg")
@click.version_option(__version__, prog_name="chatimg")
@click.option(
    "--tree",
    is_flag=True,
    is_eager=True,
    expose_value=False,
    callback=_print_cli_tree,
    help="Print the registered command tree.",
)
def main() -> None:
    """ChatImg image generation tools."""
    pass


@main.group()
def liblib():
    """LiblibAI tools."""
    pass


@liblib.command(name="generate")
@click.argument("prompt", required=False)
@click.option("--model-id", help="Model ID for generation (required).")
@click.option("--output", "-o", help="Optional output file path to download the image.")
@add_interactive_option
def liblib_generate(prompt, model_id, output, interactive):
    """Generate an image using LiblibAI."""
    inputs = resolve_command_inputs(
        schema=PROMPT_SCHEMA,
        provided={"prompt": prompt},
        interactive=interactive,
        usage="Usage: chatimg liblib generate [PROMPT] [-i|-I]",
    )
    prompt = inputs["prompt"]

    try:
        generator = create_generator("liblib")
        click.echo("Generating image with LiblibAI...")

        kwargs = {}
        if model_id:
            kwargs["model_id"] = model_id

        result = generator.generate(prompt, **kwargs)
        click.echo(f"Image URL: {result}")

        if output and result.startswith("http"):
            download_binary(result, output)

    except Exception as e:
        raise click.ClickException(str(e)) from e


@liblib.command(name="list-models")
def liblib_list_models():
    """List available models for LiblibAI."""
    try:
        generator = create_generator("liblib")
        models = generator.get_models()
        click.echo("Available models for LiblibAI:")
        for model in models:
            click.echo(
                f"- {model.get('name', 'Unknown')} (ID: {model.get('id', 'Unknown')})"
            )
    except Exception as e:
        raise click.ClickException(str(e)) from e


@main.group()
def huggingface():
    """Hugging Face tools."""
    pass


@huggingface.command(name="generate")
@click.argument("prompt", required=False)
@click.option(
    "--output",
    "-o",
    required=False,
    help="Optional output file path. Defaults to ./generated/image_huggingface_<model>_<timestamp>.png for bytes results.",
)
@add_interactive_option
def huggingface_generate(prompt, output, interactive):
    """Generate an image using Hugging Face."""
    inputs = resolve_command_inputs(
        schema=HF_GENERATE_SCHEMA,
        provided={"prompt": prompt},
        interactive=interactive,
        usage="Usage: chatimg huggingface generate [PROMPT] [-o PATH] [-i|-I]",
    )
    prompt = inputs["prompt"]

    try:
        from chatimg.image.huggingface import HuggingFaceImageGenerator

        generator = create_generator("huggingface")
        click.echo("Generating image with Hugging Face...")
        result = generator.generate(prompt)

        if isinstance(result, bytes):
            output_path = resolve_generated_output_path(
                output,
                provider="huggingface",
                model=HuggingFaceImageGenerator.DEFAULT_MODEL,
            )
            save_binary(result, output_path)
            click.echo(f"Image saved to {output_path}")
        else:
            click.echo(f"Result: {result}")
    except Exception as e:
        raise click.ClickException(str(e)) from e


@main.group()
def tongyi():
    """Tongyi Wanxiang tools."""
    pass


@tongyi.command(name="generate")
@click.argument("prompt", required=False)
@click.option("--style", default="<auto>", help="Image style.")
@click.option("--size", default="1024*1024", help="Image size.")
@click.option("--output", "-o", help="Optional output file path to download the image.")
@add_interactive_option
def tongyi_generate(prompt, style, size, output, interactive):
    """Generate an image using Tongyi Wanxiang."""
    inputs = resolve_command_inputs(
        schema=PROMPT_SCHEMA,
        provided={"prompt": prompt},
        interactive=interactive,
        usage="Usage: chatimg tongyi generate [PROMPT] [-i|-I]",
    )
    prompt = inputs["prompt"]

    try:
        generator = create_generator("tongyi")
        click.echo("Generating image with Tongyi Wanxiang...")
        result = generator.generate(prompt, style=style, size=size)

        # Tongyi returns a list of dicts with 'url'
        if isinstance(result, list):
            for i, item in enumerate(result):
                url = item.get("url")
                click.echo(f"Image {i + 1}: {url}")
                if output and url:
                    download_binary(url, output)
        else:
            click.echo(f"Result: {result}")

    except Exception as e:
        raise click.ClickException(str(e)) from e


@main.group()
def pollinations():
    """Pollinations.ai tools."""
    pass


@pollinations.command(name="generate")
@click.argument("prompt", required=False)
@click.option("--model", help="Model name (flux, turbo, etc).")
@click.option("--width", default=1024, help="Image width.")
@click.option("--height", default=1024, help="Image height.")
@click.option("--output", "-o", help="Optional output file path to download the image.")
@add_interactive_option
def pollinations_generate(prompt, model, width, height, output, interactive):
    """Generate an image using Pollinations.ai."""
    inputs = resolve_command_inputs(
        schema=PROMPT_SCHEMA,
        provided={"prompt": prompt},
        interactive=interactive,
        usage="Usage: chatimg pollinations generate [PROMPT] [-i|-I]",
    )
    prompt = inputs["prompt"]

    try:
        from chatimg.config import PollinationsConfig
        from chatimg.image import create_generator

        model = model or PollinationsConfig.POLLINATIONS_MODEL_ID.value or "flux"
        generator = create_generator("pollinations", model=model)
        click.echo(f"Generating image with Pollinations.ai (model: {model})...")
        result = generator.generate(prompt, width=width, height=height)

        for i, url in enumerate(result):
            click.echo(f"Image URL: {url}")

            if output:
                click.echo(f"Downloading to {output}...")
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }
                if PollinationsConfig.POLLINATIONS_API_KEY.value:
                    headers["Authorization"] = (
                        f"Bearer {PollinationsConfig.POLLINATIONS_API_KEY.value}"
                    )

                download_binary(url, output, headers=headers)

    except Exception as e:
        raise click.ClickException(str(e)) from e


@pollinations.command(name="list-models")
def pollinations_list_models():
    """List available image models for Pollinations.ai."""
    try:
        from chatimg.image import create_generator

        generator = create_generator("pollinations")
        models = generator.get_models()
        echo_model_list(models, "Available image models for Pollinations.ai:")
    except Exception as e:
        raise click.ClickException(str(e)) from e


@main.group()
def siliconflow():
    """SiliconFlow tools."""
    pass



@main.group()
def openai():
    """OpenAI-compatible Images API tools, including CRS proxy."""
    pass


@openai.command(name="generate")
@click.argument("prompt", required=False)
@click.option("--model", "image_model", help="Image model or preset, e.g. gpt-image-2-medium.")
@click.option("--size", default="1024x1024", show_default=True, help="Image size.")
@click.option("--quality", type=click.Choice(["low", "medium", "high", "auto"]), help="Image quality.")
@click.option("--api-base", help="Override OPENAI_API_BASE, usually ending with /v1.")
@click.option("--timeout", type=float, help="Request timeout in seconds.")
@click.option(
    "--output",
    "-o",
    help="Optional output file path. Defaults to ./generated/image_openai_<model>_<timestamp>.png",
)
@add_interactive_option
def openai_generate(prompt, image_model, size, quality, api_base, timeout, output, interactive):
    """Generate an image using OpenAI-compatible Images API."""
    inputs = resolve_command_inputs(
        schema=PROMPT_SCHEMA,
        provided={"prompt": prompt},
        interactive=interactive,
        usage="Usage: chatimg openai generate [PROMPT] [-i|-I]",
    )
    prompt = inputs["prompt"]

    try:
        generator = create_generator(
            "openai",
            api_base=api_base,
            image_model=image_model,
            timeout_seconds=timeout,
        )
        click.echo(f"Generating image with OpenAI-compatible API (image: {generator.image_model})...")
        result = generator.generate(prompt, size=size, quality=quality)
        output_path = resolve_generated_output_path(
            output,
            provider="openai",
            model=generator.image_model,
            prompt=prompt,
        )
        saved = save_binary(result, output_path)
        click.echo(f"Image saved to {saved}")
    except Exception as e:
        raise click.ClickException(str(e)) from e

@main.group()
def codex():
    """ChatGPT/Codex OAuth image tools."""
    pass


@codex.command(name="auth-status")
@click.option("--profile", default="default", show_default=True, help="OpenAI ChatEnv profile name.")
def codex_auth_status(profile):
    """Show safe OpenAI OAuth profile status without token values."""
    try:
        from chatimg.image.codex import CodexImageGenerator

        generator = CodexImageGenerator(profile=profile)
        click.echo(f"OpenAI profile: {generator.profile}")
        click.echo(f"OpenAI env file: {generator.active_env_path}")
        click.echo(f"OpenAI token store: {generator.token_store_path}")
        click.echo(f"Access token: {'present' if generator.access_token else 'missing'}")
        click.echo(f"Refresh token: {'present' if generator.refresh_token else 'missing'}")
        click.echo(
            "Access token expires at: "
            f"{generator.access_token_expires_at or 'unknown'}"
        )
        click.echo(f"Host model: {generator.host_model}")
        click.echo(f"Image model: {generator.image_model}")
    except Exception as e:
        raise click.ClickException(str(e)) from e


@codex.command(name="auth-refresh")
@click.option("--profile", default="default", show_default=True, help="OpenAI ChatEnv profile name.")
def codex_auth_refresh(profile):
    """Refresh OpenAI OAuth tokens and persist the runtime token store."""
    try:
        from chatimg.image.codex import CodexImageGenerator

        generator = CodexImageGenerator(profile=profile)
        generator.refresh_access_token()
        click.echo(
            "OpenAI OAuth tokens refreshed and saved to "
            f"{generator.token_store_path}"
        )
        click.echo(
            "Access token expires at: "
            f"{generator.access_token_expires_at or 'unknown'}"
        )
    except Exception as e:
        raise click.ClickException(str(e)) from e


@siliconflow.command(name="generate")
@click.argument("prompt", required=False)
@click.option("--model", help="Model name.")
@click.option("--size", default="1024x1024", help="Image size (e.g., 1024x1024).")
@click.option("--output", "-o", help="Optional output file path to download the image.")
@add_interactive_option
def siliconflow_generate(prompt, model, size, output, interactive):
    """Generate an image using SiliconFlow API."""
    inputs = resolve_command_inputs(
        schema=PROMPT_SCHEMA,
        provided={"prompt": prompt},
        interactive=interactive,
        usage="Usage: chatimg siliconflow generate [PROMPT] [-i|-I]",
    )
    prompt = inputs["prompt"]

    try:
        from chatimg.config import SiliconFlowConfig
        from chatimg.image import create_generator

        # Determine model
        model = (
            model
            or SiliconFlowConfig.SILICONFLOW_MODEL_ID.value
            or "black-forest-labs/FLUX.1-schnell"
        )

        generator = create_generator("siliconflow")
        click.echo(f"Generating image with SiliconFlow (model: {model})...")

        result = generator.generate(prompt, model=model, size=size)

        for i, url in enumerate(result):
            click.echo(f"Image URL: {url}")

            if output:
                click.echo(f"Downloading to {output}...")
                download_binary(url, output)

    except Exception as e:
        raise click.ClickException(str(e)) from e


@siliconflow.command(name="list-models")
def siliconflow_list_models():
    """List available image models for SiliconFlow."""
    try:
        from chatimg.image import create_generator

        generator = create_generator("siliconflow")
        models = generator.get_models()

        # Filter for text-to-image models only if possible
        image_models = []
        for m in models:
            # Check type or sub_type
            is_image = m.get("type") == "image" or m.get("sub_type") == "text-to-image"
            if is_image:
                image_models.append(m)

        if not image_models:
            image_models = models

        click.echo("Available image models for SiliconFlow:")
        for model in image_models:
            model_id = model.get("id")
            # Check if it's a free model (no Pro/ prefix)
            is_free = not model_id.startswith("Pro/")
            price_info = "FREE" if is_free else "PAID"

            click.echo(f"- {model_id} [{price_info}]")

    except Exception as e:
        raise click.ClickException(str(e)) from e


@codex.command(name="generate")
@click.argument("prompt", required=False)
@click.option(
    "--aspect-ratio",
    type=click.Choice(["square", "landscape", "portrait"]),
    help="Image aspect ratio.",
)
@click.option(
    "--image-model",
    type=click.Choice(
        ["gpt-image-2-low", "gpt-image-2-medium", "gpt-image-2-high"]
    ),
    help="Codex image model preset.",
)
@click.option(
    "--host-model",
    help="Codex host model used to invoke the image_generation tool.",
)
@click.option(
    "--base-url",
    help="Override the Codex backend base URL. The OAuth token is sent to this host.",
)
@click.option("--profile", default="default", show_default=True, help="OpenAI ChatEnv profile name.")
@click.option(
    "--timeout",
    type=float,
    help="Request timeout in seconds.",
)
@click.option(
    "--output",
    "-o",
    help="Optional output file path. Defaults to ./generated/image_codex_<model>_<timestamp>.png",
)
@add_interactive_option
def codex_generate(
    prompt,
    aspect_ratio,
    image_model,
    host_model,
    base_url,
    profile,
    timeout,
    output,
    interactive,
):
    """Generate an image using the ChatGPT/Codex OAuth image bridge."""
    inputs = resolve_command_inputs(
        schema=PROMPT_SCHEMA,
        provided={"prompt": prompt},
        interactive=interactive,
        usage="Usage: chatimg codex generate [PROMPT] [-i|-I]",
    )
    prompt = inputs["prompt"]

    try:
        generator = create_generator(
            "codex",
            base_url=base_url,
            host_model=host_model,
            image_model=image_model,
            aspect_ratio=aspect_ratio,
            timeout_seconds=timeout,
            profile=profile,
        )
        click.echo(
            "Generating image with Codex "
            f"(host: {generator.host_model}, image: {generator.image_model})..."
        )
        result = generator.generate(prompt)
        output_path = resolve_generated_output_path(
            output,
            provider="codex",
            model=generator.image_model,
            prompt=prompt,
        )
        saved = save_binary(result, output_path)
        click.echo(f"Image saved to {saved}")
    except Exception as e:
        raise click.ClickException(str(e)) from e


@codex.command(name="list-models")
@click.option("--profile", default="default", show_default=True, help="OpenAI ChatEnv profile name.")
def codex_list_models(profile):
    """List built-in Codex image model presets."""
    try:
        generator = create_generator("codex", profile=profile)
        models = generator.get_models()
        echo_model_list(models, "Available image models for Codex:")
    except Exception as e:
        raise click.ClickException(str(e)) from e


if __name__ == "__main__":
    main()
