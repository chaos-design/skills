/**
 * One command rendered as wrapping tokens.
 *
 * Splitting on spaces and letting flex wrap do the work keeps whole arguments
 * together — a line never ends with `--sk` or a chopped skill name — and shows
 * every character, so nothing has to be scrolled sideways to be read. Only the
 * repository URL is allowed to break mid-token, because it has no spaces to
 * wrap at.
 */
export function CommandLine({
  command,
  caret = false,
  dollar = true,
}: {
  command: string;
  caret?: boolean;
  /** Off for the Prompt tab, where there is no shell to speak of. */
  dollar?: boolean;
}) {
  // Tokens are positional and never reorder. Ids are assigned while the list is
  // built so React keys stay stable without leaning on the map index in JSX.
  let position = 0;
  const tokens = command
    .split(" ")
    .filter(Boolean)
    .map((token) => ({ id: `${token}@${position++}`, token }));

  return (
    <span className="flex min-w-0 flex-wrap items-baseline gap-x-[1ch] gap-y-1 text-left">
      {dollar && <span className="text-muted-foreground">$</span>}
      {tokens.map(({ id, token }, index) => (
        <span
          key={id}
          className={
            token.includes("://")
              ? "break-all text-muted-foreground"
              : index === tokens.length - 1 && !token.startsWith("--")
                ? "whitespace-nowrap text-foreground"
                : "whitespace-nowrap text-muted-foreground"
          }
        >
          {token}
        </span>
      ))}
      {caret && (
        <span aria-hidden="true" className="w-[0.6em] shrink-0 bg-foreground animate-caret">
          &nbsp;
        </span>
      )}
    </span>
  );
}
