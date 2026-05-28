"""Smoke test the caption adapter offline (no API calls)."""

from instagram_caption import build_post
from safety import check_caption


SAMPLE_BRIEF = """## Conventional wisdom
Wrapping brisket in butcher paper at 165F is the only way to push through
the stall without ruining bark.

## The pushback
Aaron Franklin himself has said he wraps later than most teach, and several
competition cooks in [1] argue no-wrap produces a deeper bark with only a
30-minute cook-time penalty. AmazingRibs' tests in [2] showed bark
moisture differences smaller than the variance between two briskets.

## VERDICT
The wrap-at-165 rule is cargo-cult — wrap by feel (probe slides like warm
butter through fat) or skip the wrap entirely on a humid pit.

## Try this weekend
- Run two flats side-by-side: one wrapped at 165, one no-wrap. Compare bark.
- Spritz hourly with 50/50 water + cider vinegar instead of wrapping.

## Sources
[1] https://amazingribs.com/tested-recipes/beef-and-bison-recipes/brisket-recipe
[2] https://heygrillhey.com/texas-style-smoked-brisket/
"""


def main():
    post = build_post("brisket bark and pellicle", SAMPLE_BRIEF)
    check_caption(post.caption)

    assert post.caption.startswith("The wrap-at-165 rule"), \
        f"hook not extracted, caption starts: {post.caption[:80]!r}"
    assert "#brisket" in post.caption, "topic hashtag missing"
    assert "#jerseysmokebbq" in post.caption, "brand hashtag missing"
    assert "amazingribs.com" in post.first_comment, "source URL missing from first comment"
    assert len(post.caption) <= 2200, f"caption too long: {len(post.caption)}"
    assert "##" not in post.caption, "markdown headers leaked into caption"

    print("OK: caption adapter passes all checks")
    print(f"    caption length: {len(post.caption)} chars")
    print(f"    hashtags: {len(post.hashtags)}")
    print()
    print("--- caption preview ---")
    print(post.caption)
    print()
    print("--- first comment preview ---")
    print(post.first_comment)


if __name__ == "__main__":
    main()
