"""Smoke test the caption adapter offline (no API calls)."""

from instagram_caption import build_post
from safety import check_caption


SAMPLE_BRIEF = """VERDICT: The wrap-at-165 rule is cargo-cult — wrap by feel, not by thermometer.

The Lie:
Most backyard tutorials say wrap brisket in butcher paper at exactly 165F to push through the stall.

Do This Instead:
1. Probe the flat at 30 min intervals starting at 160F internal.
2. Wrap only when probe slides through point fat with under 2 lbs of force.
3. Spritz the unwrapped surface every 45 min with 50/50 water + cider vinegar.
4. Pull at 203F internal, rest 1 hour in a 150F oven.

Why It Works:
AmazingRibs lab tests in [1] showed temperature-triggered wrapping varies bark moisture by less than the variance between two briskets — probe feel is the real signal.

Sources:
[1] https://amazingribs.com/tested-recipes/beef-and-bison-recipes/brisket-recipe
[2] https://heygrillhey.com/texas-style-smoked-brisket/

Featured: amazingribs
"""


def main():
    post = build_post("brisket bark and pellicle", SAMPLE_BRIEF)
    check_caption(post.caption)

    assert post.caption.startswith("The wrap-at-165 rule"), \
        f"hook not extracted, caption starts: {post.caption[:80]!r}"
    assert post.caption.count("wrap-at-165") == 1, \
        "VERDICT line duplicated in body — _strip_verdict_block broken"
    assert "Save this for your next cook" in post.caption, "save CTA missing"
    assert "Featuring @amazingribs" in post.caption, "featured @-tag missing or wrong"
    assert post.caption.count("@amazingribs") == 1, "@-tag duplicated"
    assert "Featured: amazingribs" not in post.caption, "raw Featured: line leaked into caption"
    assert "#brisket" in post.caption, "topic hashtag missing"
    assert "#jerseysmokebbq" in post.caption, "brand hashtag missing"
    assert "amazingribs.com" in post.first_comment, "source URL missing from first comment"
    assert "amazingribs.com" not in post.caption, "source URLs leaked into caption"
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
