import json
from typing import Any
from urllib.parse import quote

from fastapi.responses import HTMLResponse

from framex.config import settings


def build_docs_action_button_views(action_buttons: list[Any]) -> list[dict[str, Any]]:
    return [
        {
            "index": index,
            "title": button.title,
            "variant": button.variant,
            "requires_confirmation": button.requires_confirmation,
            "confirmation_message": button.confirmation_message,
            "auth_type": button.auth.type,
            "inputs": [
                {
                    "name": input_config.name,
                    "label": input_config.label,
                    "placeholder": input_config.placeholder,
                    "default": input_config.default,
                    "required": input_config.required,
                    "target": input_config.target,
                }
                for input_config in button.inputs
            ],
        }
        for index, button in enumerate(action_buttons)
    ]


def build_swagger_ui_html(
    openapi_url: str,
    title: str,
    action_buttons: list[dict[str, Any]] | None = None,
) -> HTMLResponse:
    docs_action_buttons = json.dumps(action_buttons or [], ensure_ascii=False)
    return HTMLResponse(
        f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{title}</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist/swagger-ui.css" />
    <style>
        :root {{
            --fx-bg: #f6f8fb;
            --fx-card: #ffffff;
            --fx-border: #e6eaf0;
            --fx-border-soft: #eef2f6;
            --fx-text: #1f2a37;
            --fx-text-soft: #475467;
            --fx-text-muted: #98a2b3;
            --fx-link: #175cd3;
            --fx-link-hover: #1849a9;
            --fx-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
        }}

        html, body {{
            margin: 0;
            padding: 0;
            background: var(--fx-bg);
        }}

        body {{
            font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont,
                "Segoe UI", sans-serif;
            color: var(--fx-text);
        }}

        .swagger-ui {{
            max-width: 1600px;
            margin: 0 auto;
            padding: 16px 12px 28px;
        }}

        .swagger-ui .topbar {{
            display: none;
        }}

        .swagger-ui .information-container {{
            padding-bottom: 4px;
        }}

        .swagger-ui .info {{
            margin: 0 0 14px 0;
        }}

        .swagger-ui .info .title {{
            color: var(--fx-text);
            font-size: 26px;
            font-weight: 700;
            letter-spacing: 0.2px;
        }}

        .swagger-ui .scheme-container {{
            background: transparent;
            box-shadow: none;
            padding: 0;
            margin: 0 0 8px 0;
        }}

        .swagger-ui .scheme-container .auth-wrapper,
        .swagger-ui .scheme-container .authorize {{
            display: none !important;
        }}

        .swagger-ui .opblock-tag-section {{
            margin-bottom: 8px;
            border: 1px solid var(--fx-border);
            border-radius: 12px;
            overflow: hidden;
            background: var(--fx-card);
            box-shadow: var(--fx-shadow);
        }}

        .swagger-ui .opblock-tag {{
            display: grid !important;
            grid-template-columns: 420px minmax(0, 1fr) 28px;
            column-gap: 18px;
            align-items: center;
            padding: 9px 14px !important;
            margin: 0 !important;
            background: #fff;
            border-bottom: 1px solid var(--fx-border-soft);
        }}

        .swagger-ui .opblock-tag:hover {{
            background: #fafbfc;
        }}

        .swagger-ui .opblock-tag .nostyle {{
            grid-column: 1;
            min-width: 0;
            margin: 0;
            white-space: normal !important;
            word-break: break-word;
            overflow-wrap: anywhere;
            line-height: 1.3;
            font-size: 15px !important;
            font-weight: 700 !important;
            color: var(--fx-text) !important;
        }}

        .swagger-ui .opblock-tag small {{
            grid-column: 2;
            display: block !important;
            min-width: 0;
            margin: 0 !important;
            padding: 0 !important;
            white-space: normal !important;
            color: var(--fx-text-soft) !important;
            font-size: 12.5px !important;
            line-height: 1.45 !important;
        }}

        .swagger-ui .opblock-tag small .markdown {{
            margin: 0 !important;
            padding: 0 !important;
        }}

        .swagger-ui .opblock-tag small .markdown p {{
            margin: 0 !important;
            padding: 0 !important;
        }}

        .swagger-ui .opblock-tag small .markdown p:first-child {{
            margin-bottom: 3px !important;
            color: var(--fx-text) !important;
            font-size: 13.5px !important;
            line-height: 1.5 !important;
            letter-spacing: 0.05px;
            max-width: 760px;
        }}

        .swagger-ui .opblock-tag small .markdown p:first-child strong {{
            font-weight: 600 !important;
            color: var(--fx-text) !important;
        }}

        .swagger-ui .opblock-tag small .markdown p:last-child {{
            color: var(--fx-text-soft) !important;
            font-size: 12px !important;
            line-height: 1.4 !important;
        }}

        .swagger-ui .opblock-tag small a {{
            color: var(--fx-link);
            text-decoration: none;
            font-weight: 500;
        }}

        .swagger-ui .opblock-tag small a:hover {{
            color: var(--fx-link-hover);
            text-decoration: underline;
        }}

        .swagger-ui .opblock-tag > button {{
            grid-column: 3 !important;
            justify-self: end !important;
            align-self: center !important;
            margin: 0 !important;
            padding: 0 !important;
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            width: 24px;
            height: 24px;
        }}

        .swagger-ui .opblock-tag > button svg {{
            display: block !important;
            width: 20px !important;
            height: 20px !important;
            opacity: 0.75;
            transition: all 0.15s ease;
        }}

        .swagger-ui .opblock-tag:hover > button svg {{
            opacity: 1;
            transform: translateX(2px);
        }}

        .swagger-ui .opblock {{
            margin: 0 !important;
            border-radius: 0 !important;
            box-shadow: none !important;
        }}

        .swagger-ui .opblock:last-child {{
            border-bottom: none !important;
        }}

        .swagger-ui .opblock-summary-path,
        .swagger-ui .opblock-summary-description {{
            white-space: normal !important;
            word-break: break-word;
        }}

        .swagger-ui .tag-toolbar {{
            display: flex;
            justify-content: flex-end;
            gap: 8px;
            flex-wrap: wrap;
            margin: 0 0 8px 0;
        }}

        .swagger-ui .tag-toolbar button {{
            appearance: none;
            border: 1px solid var(--fx-border);
            background: #fff;
            color: var(--fx-text);
            border-radius: 8px;
            padding: 6px 12px;
            font-size: 12.5px;
            font-weight: 600;
            cursor: pointer;
            box-shadow: var(--fx-shadow);
        }}

        .swagger-ui .tag-toolbar button:hover {{
            background: #f9fafb;
        }}

        .swagger-ui .tag-toolbar .docs-action-button-primary {{
            border-color: #175cd3;
            background: #175cd3;
            color: #fff;
        }}

        .swagger-ui .tag-toolbar .docs-action-button-primary:hover {{
            background: #1849a9;
        }}

        .swagger-ui .tag-toolbar .docs-action-button-success {{
            border-color: #039855;
            background: #039855;
            color: #fff;
        }}

        .swagger-ui .tag-toolbar .docs-action-button-success:hover {{
            background: #027a48;
        }}

        .swagger-ui .tag-toolbar .docs-action-button-warning {{
            border-color: #dc6803;
            background: #dc6803;
            color: #fff;
        }}

        .swagger-ui .tag-toolbar .docs-action-button-warning:hover {{
            background: #b54708;
        }}

        .swagger-ui .tag-toolbar .docs-action-button-danger {{
            border-color: #d92d20;
            background: #d92d20;
            color: #fff;
        }}

        .swagger-ui .tag-toolbar .docs-action-button-danger:hover {{
            background: #b42318;
        }}

        .docs-action-modal-backdrop {{
            position: fixed;
            inset: 0;
            z-index: 9999;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
            background: rgba(15, 23, 42, 0.32);
        }}

        .docs-action-modal {{
            width: min(420px, 100%);
            border: 1px solid var(--fx-border);
            border-radius: 8px;
            background: #fff;
            box-shadow: 0 20px 40px rgba(15, 23, 42, 0.18);
        }}

        .docs-action-modal-header {{
            padding: 14px 16px;
            border-bottom: 1px solid var(--fx-border-soft);
            color: var(--fx-text);
            font-size: 15px;
            font-weight: 700;
        }}

        .docs-action-modal-body {{
            display: grid;
            gap: 12px;
            padding: 16px;
        }}

        .docs-action-modal-field {{
            display: grid;
            gap: 6px;
        }}

        .docs-action-modal-field label {{
            color: var(--fx-text);
            font-size: 12.5px;
            font-weight: 600;
        }}

        .docs-action-modal-field input {{
            width: 100%;
            box-sizing: border-box;
            border: 1px solid var(--fx-border);
            border-radius: 6px;
            padding: 8px 10px;
            color: var(--fx-text);
            font-size: 13px;
        }}

        .docs-action-modal-footer {{
            display: flex;
            justify-content: flex-end;
            gap: 8px;
            padding: 12px 16px 16px;
        }}

        .docs-action-modal-footer button {{
            appearance: none;
            border: 1px solid var(--fx-border);
            border-radius: 8px;
            background: #fff;
            color: var(--fx-text);
            padding: 7px 12px;
            font-size: 12.5px;
            font-weight: 600;
            cursor: pointer;
        }}

        .docs-action-modal-footer button[type="submit"] {{
            border-color: var(--fx-link);
            background: var(--fx-link);
            color: #fff;
        }}

        @media (max-width: 1400px) {{
            .swagger-ui .opblock-tag {{
                grid-template-columns: 360px minmax(0, 1fr) 28px;
            }}

            .swagger-ui .opblock-tag small .markdown p:first-child {{
                max-width: 680px;
            }}
        }}

        @media (max-width: 1100px) {{
            .swagger-ui .opblock-tag {{
                grid-template-columns: 300px minmax(0, 1fr) 28px;
                column-gap: 14px;
            }}

            .swagger-ui .opblock-tag small .markdown p:first-child {{
                max-width: none;
            }}
        }}

        @media (max-width: 900px) {{
            .swagger-ui .opblock-tag {{
                grid-template-columns: 1fr;
                row-gap: 6px;
            }}

            .swagger-ui .opblock-tag .nostyle,
            .swagger-ui .opblock-tag small,
            .swagger-ui .opblock-tag > button {{
                grid-column: auto !important;
            }}

            .swagger-ui .opblock-tag > button {{
                justify-self: end !important;
            }}
        }}
    </style>
</head>
<body>
    <div id="swagger-ui"></div>

    <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist/swagger-ui-bundle.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist/swagger-ui-standalone-preset.js"></script>
    <script>
        let allExpanded = false;
        const docsActionButtons = {docs_action_buttons};

        function getTagSections() {{
            return Array.from(document.querySelectorAll(".swagger-ui .opblock-tag-section"));
        }}

        function isExpanded(section) {{
            return !!section.querySelector(".opblock");
        }}

        function toggleTag(section, expand) {{
            const expanded = isExpanded(section);
            if (expanded === expand) return;

            const btn = section.querySelector(".opblock-tag > button");
            if (btn) btn.click();
        }}

        function syncToolbarText() {{
            const btn = document.getElementById("toggle-all-tags");
            if (!btn) return;
            btn.innerText = allExpanded ? "收起全部" : "展开全部";
        }}

        function toggleAllTags() {{
            const sections = getTagSections();
            allExpanded = !allExpanded;

            sections.forEach((section, index) => {{
                setTimeout(() => toggleTag(section, allExpanded), index * 20);
            }});

            syncToolbarText();
        }}

        function collectDocsActionInputs(buttonConfig) {{
            const inputs = Array.isArray(buttonConfig.inputs) ? buttonConfig.inputs : [];
            if (inputs.length === 0) {{
                return Promise.resolve({{}});
            }}

            return new Promise((resolve) => {{
                const backdrop = document.createElement("div");
                backdrop.className = "docs-action-modal-backdrop";

                const modal = document.createElement("form");
                modal.className = "docs-action-modal";
                modal.noValidate = false;

                const header = document.createElement("div");
                header.className = "docs-action-modal-header";
                header.textContent = buttonConfig.title || "执行操作";
                modal.appendChild(header);

                const body = document.createElement("div");
                body.className = "docs-action-modal-body";

                inputs.forEach((inputConfig, inputIndex) => {{
                    const field = document.createElement("div");
                    field.className = "docs-action-modal-field";

                    const inputId = "docs-action-input-" + buttonConfig.index + "-" + inputIndex;
                    const label = document.createElement("label");
                    label.htmlFor = inputId;
                    label.textContent = (inputConfig.label || inputConfig.name || "Input") + (inputConfig.required ? " *" : "");

                    const input = document.createElement("input");
                    input.id = inputId;
                    input.name = inputConfig.name || "";
                    input.type = "text";
                    input.placeholder = inputConfig.placeholder || "";
                    input.value = inputConfig.default || "";
                    input.required = !!inputConfig.required;

                    field.appendChild(label);
                    field.appendChild(input);
                    body.appendChild(field);
                }});

                modal.appendChild(body);

                const footer = document.createElement("div");
                footer.className = "docs-action-modal-footer";

                const cancelButton = document.createElement("button");
                cancelButton.type = "button";
                cancelButton.textContent = "取消";

                const submitButton = document.createElement("button");
                submitButton.type = "submit";
                submitButton.textContent = "执行";

                footer.appendChild(cancelButton);
                footer.appendChild(submitButton);
                modal.appendChild(footer);
                backdrop.appendChild(modal);
                document.body.appendChild(backdrop);

                const close = (value) => {{
                    backdrop.remove();
                    resolve(value);
                }};

                cancelButton.addEventListener("click", () => close(null));
                backdrop.addEventListener("click", (event) => {{
                    if (event.target === backdrop) {{
                        close(null);
                    }}
                }});

                modal.addEventListener("submit", (event) => {{
                    event.preventDefault();
                    if (!modal.reportValidity()) {{
                        return;
                    }}

                    const values = {{}};
                    Array.from(modal.querySelectorAll("input[name]")).forEach((input) => {{
                        values[input.name] = input.value;
                    }});
                    close(values);
                }});

                const firstInput = modal.querySelector("input");
                if (firstInput) {{
                    firstInput.focus();
                    firstInput.select();
                }}
            }});
        }}

        async function invokeDocsActionButton(buttonConfig, triggerButton) {{
            if (buttonConfig.requires_confirmation) {{
                const confirmationMessage = buttonConfig.confirmation_message || ("确认执行: " + (buttonConfig.title || "执行操作") + "?");
                if (!window.confirm(confirmationMessage)) {{
                    return;
                }}
            }}

            const inputValues = await collectDocsActionInputs(buttonConfig);
            if (inputValues === null) {{
                return;
            }}

            const authPayload = {{}};
            if (buttonConfig.auth_type === "password") {{
                const password = window.prompt("请输入操作密码");
                if (password === null) {{
                    return;
                }}
                authPayload.password = password;
            }}

            const originalText = triggerButton.textContent;
            triggerButton.disabled = true;
            triggerButton.textContent = "请求中...";

            try {{
                const response = await fetch("/docs/action-buttons/" + buttonConfig.index + "/invoke", {{
                    method: "POST",
                    credentials: "same-origin",
                    headers: {{
                        "Content-Type": "application/json"
                    }},
                    body: JSON.stringify({{
                        inputs: inputValues,
                        auth: authPayload
                    }})
                }});

                const responseText = await response.text();
                let data = null;
                try {{
                    data = JSON.parse(responseText);
                }} catch (_error) {{
                    data = null;
                }}

                if (data && Object.prototype.hasOwnProperty.call(data, "body")) {{
                    alert("状态码: " + data.status_code + "\\n\\n" + data.body);
                    return;
                }}

                alert("状态码: " + response.status + "\\n\\n" + responseText);
            }} catch (error) {{
                alert("请求失败: " + error);
            }} finally {{
                triggerButton.disabled = false;
                triggerButton.textContent = originalText;
            }}
        }}

        function insertToolbar() {{
            if (document.querySelector(".swagger-ui .tag-toolbar")) return;

            const firstTagSection = document.querySelector(".swagger-ui .opblock-tag-section");
            if (!firstTagSection) return;

            const toolbar = document.createElement("div");
            toolbar.className = "tag-toolbar";

            docsActionButtons.forEach((buttonConfig) => {{
                const actionButton = document.createElement("button");
                actionButton.type = "button";
                actionButton.className = "docs-action-button-" + (buttonConfig.variant || "default");
                actionButton.textContent = buttonConfig.title || "执行操作";
                actionButton.addEventListener("click", () => invokeDocsActionButton(buttonConfig, actionButton));
                toolbar.appendChild(actionButton);
            }});

            const toggleButton = document.createElement("button");
            toggleButton.type = "button";
            toggleButton.id = "toggle-all-tags";
            toggleButton.textContent = "展开全部";
            toolbar.appendChild(toggleButton);

            firstTagSection.parentNode.insertBefore(toolbar, firstTagSection);

            toggleButton.addEventListener("click", toggleAllTags);

            syncToolbarText();
        }}

        function getTagDescriptionLink(target) {{
            const link = target.closest(".swagger-ui .opblock-tag small a");
            return link instanceof HTMLAnchorElement ? link : null;
        }}

        function hydrateLatestReleaseLinks() {{
            const releaseLinks = document.querySelectorAll('.swagger-ui .opblock-tag small a[href*="/docs/plugin-release?plugin="]');
            releaseLinks.forEach((link) => {{
                if (!(link instanceof HTMLAnchorElement) || link.dataset.releaseHydrated === "true") {{
                    return;
                }}

                link.dataset.releaseHydrated = "true";
                fetch(link.href, {{ credentials: "same-origin" }})
                    .then((response) => response.ok ? response.json() : null)
                    .then((data) => {{
                        if (!data || !data.has_update || !data.latest_version) {{
                            link.remove();
                            return;
                        }}

                        link.textContent = "⬆️ 发现新版本: " + data.latest_version;
                        if (data.repo_url) {{
                            link.href = data.repo_url;
                        }}
                    }})
                    .catch(() => {{
                        link.remove();
                    }});
            }});
        }}

        document.addEventListener("pointerdown", (event) => {{
            const link = getTagDescriptionLink(event.target);
            if (!link) return;

            event.stopPropagation();
            if (link.href.includes("/docs/plugin-config?plugin=")) {{
                event.preventDefault();
            }}
        }}, true);

        document.addEventListener("click", (event) => {{
            const link = getTagDescriptionLink(event.target);
            if (!link) return;

            event.stopPropagation();
            if (!link.href.includes("/docs/plugin-config?plugin=")) {{
                return;
            }}

            event.preventDefault();
            window.open(link.href, "_blank", "noopener,noreferrer");
        }}, true);

        window.ui = SwaggerUIBundle({{
            url: "{openapi_url}",
            dom_id: "#swagger-ui",
            deepLinking: true,
            docExpansion: "none",
            defaultModelsExpandDepth: -1,
            displayRequestDuration: true,
            presets: [
                SwaggerUIBundle.presets.apis,
                SwaggerUIStandalonePreset
            ],
            layout: "BaseLayout",
            onComplete: function() {{
                insertToolbar();
                hydrateLatestReleaseLinks();
            }}
        }});

        const observer = new MutationObserver(() => {{
            insertToolbar();
            hydrateLatestReleaseLinks();
        }});

        observer.observe(document.body, {{
            childList: true,
            subtree: true
        }});
    </script>
</body>
</html>
        """
    )


def _format_plugin_release_view(plugin_name: str | None = None) -> str:
    if not plugin_name:
        return ""
    plugin_query = quote(plugin_name)
    return f" [](/docs/plugin-release?plugin={plugin_query})"


def _format_plugin_config_view(plugin_name: str | None = None) -> str:
    if not plugin_name or not settings.auth.oauth:
        return ""
    plugin_query = quote(plugin_name)
    return f"[⚙️ View Config](/docs/plugin-config?plugin={plugin_query})"


def build_plugin_description(
    author: str,
    version: str,
    description: str,
    repo: str,
    plugin_name: str | None = None,
) -> str:

    latest_release = _format_plugin_release_view(plugin_name)
    config_view = _format_plugin_config_view(plugin_name)
    config_suffix = f" · {config_view}" if config_view else ""
    return f"**{description}**{latest_release}\n\n\n👤 {author} · 🧩 {version} · [🔗 Repo]({repo}){config_suffix}"
