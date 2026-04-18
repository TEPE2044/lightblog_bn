from typing import Dict, List

import bleach

# allowed_elements
ALLOWED_ELMS = [
    "p", "br", "strong", "b", "em", "i", "u", "s",
    "h1", "h2", "h3", "blockquote", "a", "img",
    "ul", "ol", "li", "div", "span", "table", "tbody", "tr", "td",
    "hr", "pre", "code", "iframe"
]
# allowed_attributes
ALLOWED_ATBS: Dict[str, List[str]] = {
    "a": ["href", "title", "target"],
    "img": ["src", "alt", "title", "width", "height"],
    "div": ["class", "style"],
    "span": ["class", "style"],
    "table": ["width", "border"],
    "code": ["class"],
    "p": ["style"],
    "iframe": ["frameborder", "border", "marginwidth", "marginheight", "width", "height", "src"]
}


async def clean_content(content: str) -> str:
    return bleach.clean(
        content,
        tags=ALLOWED_ELMS,
        attributes=ALLOWED_ATBS,
        strip=True,
        strip_comments=True
    )
