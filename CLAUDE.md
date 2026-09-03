# CLAUDE.md

Guidance for Claude Code working in this repo. See `README.md` for the project overview.

## Working style

- **Keep responses under 10 lines.** Hard cap, not a preference. Longer only
  when the ask is itself a report/walkthrough, or a table is the answer. Code
  and command output don't count; prose around them does. If an explanation
  needs more, it belongs in `docs/` or a comment, not the reply.
- **No em-dash.** Never use the em-dash character; use a plain hyphen `-`.
  Applies everywhere: chat, code, comments, docs, commits.
- **User handles git commits.** Never commit on their behalf or offer to (`mc`
  below is the one exception). Never add `Co-Authored-By` or other AI trailers.
  When asked to **push**, just push - no ahead/behind narration.
- **Keep the UI polished.** Prefer real buttons over text-arrow links.
- **Don't bluff confidence.** When pattern-matching instead of measuring, say
  so. When it's a coin-flip, say "either works, pick one".
- **Do what was asked, not a substitute.** If the exact thing isn't convenient,
  ask first - don't silently swap in a different approach.
- **Think before coding.** State assumptions; if multiple readings exist, name
  them instead of picking silently; if something is unclear, stop and ask.
- **Simplest thing that works.** Nothing speculative: no features beyond the
  ask, no abstractions for single-use code, no error handling for impossible
  cases.
- **Stay in the named scope.** Edit only files under the area the request names
  ("in settings" = the settings pages, not the page they link to). Anything
  outside it: **stop and ask first**, even a one-word label, even when it looks
  like part of the same feature. "It's related" is not permission - that is
  exactly the reasoning that edited the main kits page when the ask said
  settings. Check the file list against the named scope *before* editing, not
  after. Don't refactor or reformat adjacent code; mention unrelated dead code
  rather than deleting it. Do clean up orphans your own change created.
- **Verify.** For non-trivial changes, name the check that proves it works
  (test, curl, query) and run it.
- For commit messages, only describe the latest diff unless asked otherwise.

**Shortcut: `mc`** - when the user sends just `mc` (optionally with a hint):
split the uncommitted changes into **one commit per feature** and create those
commits. Run `git status` + `git diff HEAD`, group by feature (staging each
group's files explicitly), write a concise title + body for each. Check
`git log --oneline -10` for style. No em-dash, no AI trailers. 
Commit directly (sending `mc` is the authorization).
