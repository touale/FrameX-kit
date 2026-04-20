from urllib.parse import quote

from fastapi.responses import HTMLResponse

from framex.config import settings


def build_swagger_ui_html(openapi_url: str, title: str) -> HTMLResponse:
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

        function insertToolbar() {{
            if (document.querySelector(".swagger-ui .tag-toolbar")) return;

            const firstTagSection = document.querySelector(".swagger-ui .opblock-tag-section");
            if (!firstTagSection) return;

            const toolbar = document.createElement("div");
            toolbar.className = "tag-toolbar";
            toolbar.innerHTML = `
                <button type="button" id="toggle-all-tags">展开全部</button>
            `;

            firstTagSection.parentNode.insertBefore(toolbar, firstTagSection);

            document
                .getElementById("toggle-all-tags")
                .addEventListener("click", toggleAllTags);

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
