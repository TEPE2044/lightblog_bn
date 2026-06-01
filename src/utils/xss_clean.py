from typing import Dict, List

import bleach
from bleach.css_sanitizer import CSSSanitizer

# allowed_elements
ALLOWED_ELMS = [
    "p", "br", "strong", "b", "em", "i", "u", "s",
    "h1", "h2", "h3", "blockquote", "a", "img",
    "ul", "ol", "li", "div", "span", "table", "tbody", "tr", "td",
    "hr", "pre", "code", "iframe", "button"
]
# allowed_attributes
ALLOWED_ATBS: Dict[str, List[str]] = {
    "a": ["href", "title", "target"],
    "img": ["src", "alt", "title", "width", "height", "loading"],
    "div": ["class", "style", "data-w-e-type", "data-w-e-is-void", "data-music-card", "data-selected", "data-id", "data-name", "data-artist", "data-audio", "data-cover",
            "reks-music-card__cover"],
    "span": ["class", "style"],
    "table": ["width", "border"],
    "code": ["class"],
    "p": ["style"],
    "iframe": ["frameborder", "border", "marginwidth", "marginheight", "width", "height", "src"],
    "button": ["type", "data-action"]
}

CSS_SANITIZER = CSSSanitizer(
    allowed_css_properties=["color", "background-color", "text-align", "font-weight", "font-style", "text-decoration", "width", "height", "max-width", "min-width", "max-height", "min-height", "margin", "margin-left", "margin-right", "margin-top", "margin-bottom", "padding", "padding-left", "padding-right", "padding-top", "padding-bottom", "border", "border-width", "border-style", "border-color", "border-radius", "display"],
    allowed_svg_properties=[]
)


async def clean_content(content: str) -> str:
    return bleach.clean(
        content,
        tags=ALLOWED_ELMS,
        attributes=ALLOWED_ATBS,
        css_sanitizer=CSS_SANITIZER,
        strip=True,
        strip_comments=True
    )
